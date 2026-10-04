"""Durable host orchestration for the frozen Dev VNext semantic contracts.

Human authentication is supplied by the embedding host, never inferred from
artifact text. Journal frames retain canonical states and runtime observations;
the atomic state projection can be reconstructed after an interrupted publish.
"""
from contextlib import contextmanager
import copy
from datetime import datetime, timezone
from functools import wraps
import hashlib
import json
import os
from pathlib import Path
import subprocess
import stat
import tempfile
import threading

from tooling.lib import dev_vnext as dev


def _operation(function):
    @wraps(function)
    def wrapped(self, *args, **kwargs):
        with self._lock():
            return function(self, *args, **kwargs)
    return wrapped


def _read(path):
    try:
        value=json.loads(Path(path).read_text(encoding='utf-8'))
        if not isinstance(value,dict): raise ValueError('runtime document must be an object')
        return value
    except (OSError, ValueError, UnicodeError) as exc:
        raise ValueError('invalid persisted runtime document: '+str(path)) from exc


def _atomic(path, content):
    path = Path(path)
    _safe_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix='.'+path.name+'-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)


def _json(path, value):
    _atomic(path, dev.semantic_bytes(value)+b'\n')


def _stamp():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def _safe_path(path):
    for ancestor in (Path(path),*Path(path).parents):
        if ancestor.exists() or ancestor.is_symlink():
            info=ancestor.lstat()
            if stat.S_ISLNK(info.st_mode) or bool(getattr(info,'st_file_attributes',0)&0x400):
                raise ValueError('symlink/reparse runtime and mutation path forbidden')


class DevRuntime:
    """One project runtime; callers may recreate it between every operation."""
    def __init__(self, root, *, ba_authenticator=None, foundation_authenticator=None,
                 technical_authenticator=None):
        self.root = Path(root).resolve()
        self.storage = self.root / '.devkit'
        self.context = dict(ba_authenticator=ba_authenticator,
                            foundation_authenticator=foundation_authenticator,
                            technical_authenticator=technical_authenticator)
        self.state = None
        self.metadata = None
        self.frame_hash = None
        self._mutex = threading.RLock()
        self._lock_depth = 0

    @contextmanager
    def _lock(self):
        # ponytail: one project lock; separate projects already run independently.
        with self._mutex:
            _safe_path(self.storage)
            if self._lock_depth:
                self._lock_depth += 1
                try: yield
                finally: self._lock_depth -= 1
                return
            self.storage.mkdir(parents=True, exist_ok=True)
            with (self.storage / '.runtime.lock').open('a+b') as stream:
                if os.name == 'nt':
                    import msvcrt
                    stream.seek(0)
                    if not stream.read(1): stream.write(b'0'); stream.flush()
                    stream.seek(0)
                    try: msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                    except OSError as exc: raise ValueError('runtime is busy') from exc
                else:
                    import fcntl
                    try: fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    except OSError as exc: raise ValueError('runtime is busy') from exc
                self._lock_depth = 1
                try: yield
                finally:
                    self._lock_depth = 0
                    if os.name == 'nt':
                        stream.seek(0); msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
                    else: fcntl.flock(stream, fcntl.LOCK_UN)

    def reference(self, path, revision='RUNTIME-1'):
        path = Path(path)
        absolute = path.resolve() if path.is_absolute() else (self.root / path).resolve()
        try: relative = absolute.relative_to(self.root).as_posix()
        except ValueError as exc: raise ValueError('exact evidence must be under project root') from exc
        ref = dict(path=relative, revision=revision, sha256=hashlib.sha256(absolute.read_bytes()).hexdigest())
        dev._ref(ref, self.root)
        return ref

    @property
    def run_directory(self):
        if self.state is None: raise ValueError('no active run')
        return self.storage / 'runs' / self.state['run_id']

    def _artifact(self, relative, data, revision='RUNTIME-1'):
        path = self.run_directory / relative
        if path.exists():
            if path.read_bytes() != dev.semantic_bytes(data)+b'\n':
                raise ValueError('immutable runtime artifact already exists')
        else: _json(path, data)
        return self.reference(path, revision)

    def _ingest(self, value, directory, label):
        if isinstance(value, dict) and {'path','sha256','revision'} <= set(value):
            dev._ref(value, self.root)
            return copy.deepcopy(value)
        if not isinstance(value, dict):
            value = dev.read_document(Path(value).read_text(encoding='utf-8'))
        return self._artifact(directory+'/'+label+'-'+dev.digest(value)[:16]+'.json', value)

    def _git(self, root, *args):
        result = subprocess.run(['git','-C',str(root),*args], capture_output=True, text=True,
                                encoding='utf-8', errors='replace', shell=False)
        if result.returncode:
            raise ValueError('repository observation failed: git '+ ' '.join(args)+': '+result.stderr.strip())
        return result.stdout.strip()

    def _identities(self, repositories, roots):
        if set(roots) != {row['id'] for row in repositories}:
            raise ValueError('exact repository root per identity required')
        identities = {}
        for row in repositories:
            if not Path(roots[row['id']]).is_absolute(): raise ValueError('explicit absolute repository root required')
            root = Path(roots[row['id']]).resolve()
            observed = Path(self._git(root, 'rev-parse','--show-toplevel')).resolve()
            if observed != root: raise ValueError('ambiguous repository root identity')
            git_dir = Path(self._git(root,'rev-parse','--absolute-git-dir')).resolve()
            identity = dict(root=str(root), git_dir=str(git_dir))
            if any(root == Path(other['root']) or git_dir == Path(other['git_dir']) for other in identities.values()):
                raise ValueError('ambiguous duplicate repository identity')
            if self._git(root,'rev-parse','HEAD') != row['base_revision']:
                raise ValueError('intake requires exact observed repository base revision')
            identities[row['id']] = identity
        return identities

    def _repository(self, repository_id):
        if repository_id not in self.metadata['repository_identities']:
            raise ValueError('unknown repository identity')
        identity = self.metadata['repository_identities'][repository_id]
        root = Path(identity['root']).resolve()
        if str(root) != identity['root'] or Path(self._git(root,'rev-parse','--show-toplevel')).resolve() != root or str(Path(self._git(root,'rev-parse','--absolute-git-dir')).resolve()) != identity['git_dir']:
            raise ValueError('repository identity drift')
        return root

    def _paths(self, repository_id, *, clean=False):
        row = next(row for row in self.state['repositories'] if row['id']==repository_id)
        root = self._repository(repository_id)
        head = self._git(root,'rev-parse','HEAD')
        if self._git(root,'merge-base',row['base_revision'],head) != row['base_revision']:
            raise ValueError('BLOCKED: repository base revision drift')
        paths = set(filter(None,self._git(root,'diff','--name-only',row['base_revision'],head,'--').splitlines()))
        pending = set(filter(None,self._git(root,'diff','--name-only','HEAD','--').splitlines()))
        pending.update(filter(None,self._git(root,'ls-files','--others','--exclude-standard').splitlines()))
        # Runtime artifacts are orchestration storage, not implementation source.
        runtime_prefix = None
        try: runtime_prefix = self.storage.relative_to(root).as_posix()
        except ValueError: pass
        if runtime_prefix:
            pending = {path for path in pending if not (path==runtime_prefix or path.startswith(runtime_prefix+'/'))}
        if clean and pending: raise ValueError('exact final implementation revision requires clean repository')
        paths.update(pending)
        for path in paths:
            dev.portable_path(path)
            if row['role'] != 'IMPLEMENTATION' or not any(path==scope or path.startswith(scope+'/') for scope in row['allowed_write_paths']):
                raise ValueError('BLOCKED: observed source path outside approved write scope: '+path)
            self._physical_path(root,path)
        return head, sorted(paths)

    def _physical_path(self, repository_root, path):
        dev.portable_path(path)
        _safe_path(repository_root/path)
        candidate = (repository_root / path).resolve()
        if not candidate.is_relative_to(repository_root) or candidate.is_relative_to(self.storage) or path.casefold().startswith('.git/') or path.casefold()=='.git':
            raise ValueError('source path escapes approved repository or reaches runtime/control files')
        # Protect exact physical authority even when project/repository roots differ.
        if candidate in self._authority_paths(): raise ValueError('BA authority is immutable')
        return candidate

    def _authority_paths(self):
        if self.state['upstream'] is None: return set()
        document=dev._data(self.state['upstream'],self.root)
        foundation_root=document.get('project_foundation',{}).get('root','.')
        pending=[self.state['upstream']]
        seen=set()
        paths=set()
        while pending:
            ref=pending.pop()
            if ref['path'] in seen: continue
            seen.add(ref['path'])
            authority=dev._ref(ref,self.root)
            paths.add(authority.resolve())
            try: document=dev.read_document(authority.read_text(encoding='utf-8'))
            except (ValueError,UnicodeError): continue
            children=list(dev._all_refs(document))
            if foundation_root!='.' and ref['path'].startswith(foundation_root+'/'):
                children=[{**child,'path':foundation_root+'/'+child['path']} for child in children]
            pending.extend(children)
        return paths

    def _scope_integrity(self):
        authority=self._authority_paths()
        for row in self.state['repositories']:
            root=self._repository(row['id'])
            for path in row['allowed_write_paths']:
                target=self._physical_path(root,path)
                if any(protected==target or protected.is_relative_to(target) for protected in authority):
                    raise ValueError('write scope overlaps physical transitive BA/Foundation authority')

    def _validate_metadata(self, metadata, state=None):
        state=self.state if state is None else state
        expected={'schema_version','start_request','repository_identities','review','verification','review_budget','blocked_reason','fix_active','mutations','workflow'}
        if not isinstance(metadata,dict) or set(metadata)!=expected or type(metadata['schema_version']) is not int or metadata['schema_version']!=2:
            raise ValueError('unsupported runtime metadata schema')
        if type(metadata['fix_active']) is not bool or not isinstance(metadata['mutations'],list) or not isinstance(metadata['workflow'],dict):
            raise ValueError('invalid runtime metadata')
        if metadata['blocked_reason'] is not None and not isinstance(metadata['blocked_reason'],str): raise ValueError('invalid block reason')
        dev._budget(metadata['review_budget'])
        if metadata['review'] is not None: dev._check(metadata['review'],dev.REVIEW)
        if metadata['verification'] is not None: dev._check(metadata['verification'],dev.VERIFICATION)
        identities=metadata['repository_identities']
        if not isinstance(identities,dict) or set(identities)!={row['id'] for row in state['repositories']}:
            raise ValueError('runtime repository identities mismatch')
        for identity in identities.values():
            if not isinstance(identity,dict) or set(identity)!={'root','git_dir'} or any(not isinstance(value,str) or not Path(value).is_absolute() for value in identity.values()):
                raise ValueError('invalid repository identity metadata')
        for mutation in metadata['mutations']:
            if not isinstance(mutation,dict) or set(mutation)!={'repository_id','source_path','content_sha256'}:
                raise ValueError('invalid persisted mutation evidence')
            dev.identifier(mutation['repository_id']); dev.portable_path(mutation['source_path'])
            dev.validate_schema(mutation['content_sha256'],dev.HASH)

    def _bases(self):
        result = {}
        for row in self.state['repositories']:
            self._paths(row['id'])
            result[row['id']] = row['base_revision']
        return result

    def _initial_base_guard(self):
        if any(event['to']=='IMPLEMENTING' for event in self.state['history']): return
        for row in self.state['repositories']:
            if self._git(self._repository(row['id']),'rev-parse','HEAD')!=row['base_revision']:
                raise ValueError('BLOCKED: repository HEAD drift before implementation readiness')

    def _outputs(self, *, clean=True):
        revisions, paths = {}, {}
        for row in self.state['repositories']:
            head, changed = self._paths(row['id'],clean=clean)
            if row['role']=='IMPLEMENTATION': revisions[row['id']]=head; paths[row['id']]=changed
        return revisions, paths

    def _save(self, state=None):
        state = copy.deepcopy(self.state if state is None else state)
        dev.validate_state(state,self.root,**self.context)
        self._validate_metadata(self.metadata)
        if state['lifecycle']=='READY_FOR_TEST' and self._outputs()[0]!=state['verification']['repository_revisions']:
            raise ValueError('implementation revision drift during final trusted-host validation')
        frames = sorted((self.run_directory / 'journal').glob('*.json'))
        previous = _read(frames[-1]) if frames else None
        if previous:
            if previous['sha256'] != self.frame_hash: raise ValueError('stale runtime update')
            if previous['state'] != state: dev.validate_transition(previous['state'],state)
        body = dict(schema_version=2,sequence=len(frames),previous_sha256=self.frame_hash,
                    state=state,metadata=copy.deepcopy(self.metadata))
        frame = {**body,'sha256':dev.digest(body)}
        _json(self.run_directory / 'journal' / f'{len(frames):08d}.json',frame)
        _json(self.run_directory / 'state.json',state)
        self.state, self.frame_hash = state,frame['sha256']
        _json(self.storage / 'current.json',dict(schema_version=2,run_id=state['run_id']))
        return copy.deepcopy(state)

    @_operation
    def load(self, run_id=None, *, validate=True):
        _safe_path(self.storage/'runs')
        if run_id is None:
            if self.state is not None: run_id=self.state['run_id']
            else:
                current = _read(self.storage / 'current.json')
                if current.get('schema_version') != 2 or set(current) != {'schema_version','run_id'}:
                    raise ValueError('unsupported current runtime schema')
                run_id = current['run_id']
        dev.identifier(run_id)
        directory = self.storage / 'runs' / run_id
        _safe_path(directory/'journal')
        projected = _read(directory / 'state.json')
        frames = sorted((directory / 'journal').glob('*.json'))
        if not frames: raise ValueError('persisted runtime requires durable history')
        prior = None
        for sequence,path in enumerate(frames):
            frame = _read(path)
            if path.name != f'{sequence:08d}.json' or set(frame) != {'schema_version','sequence','previous_sha256','state','metadata','sha256'}:
                raise ValueError('runtime history mismatch')
            body = {key:value for key,value in frame.items() if key!='sha256'}
            if type(frame['schema_version']) is not int or frame['schema_version']!=2 or type(frame['sequence']) is not int or frame['sequence']!=sequence or dev.digest(body)!=frame['sha256'] or frame['previous_sha256']!=(prior['sha256'] if prior else None):
                raise ValueError('runtime history integrity mismatch')
            dev._check(frame['state'],dev.STATE_V2)
            self._validate_metadata(frame['metadata'],frame['state'])
            if frame['state']['run_id']!=run_id: raise ValueError('runtime identity mismatch')
            if prior and prior['state']!=frame['state']: dev.validate_transition(prior['state'],frame['state'])
            if not prior and (frame['state']['lifecycle']!='INTAKE' or frame['state']['history']):
                raise ValueError('runtime journal must start at intake')
            if prior and frame['metadata']['repository_identities']!=prior['metadata']['repository_identities']:
                raise ValueError('repository identity history drift')
            prior=frame
        allowed = [prior['state']]
        if len(frames)>1: allowed.append(_read(frames[-2])['state'])
        if projected not in allowed: raise ValueError('state projection/history mismatch')
        self.state,self.metadata,self.frame_hash = copy.deepcopy(prior['state']),copy.deepcopy(prior['metadata']),prior['sha256']
        self._validate_metadata(self.metadata)
        request_ref = self.metadata['start_request']
        request = dev._data(request_ref,self.root)
        if self._request_state(request)!=_read(frames[0])['state']:
            raise ValueError('intake request/state binding drift')
        if {key:str(Path(value).resolve()) for key,value in request['repository_roots'].items()}!={key:value['root'] for key,value in self.metadata['repository_identities'].items()}:
            raise ValueError('repository identity/intake binding drift')
        for ref in dev._all_refs(self.metadata): dev._ref(ref,self.root)
        if validate: dev.validate_state(self.state,self.root,**self.context)
        self._bases()
        if validate and self.state['lifecycle']!='INTAKE': self._scope_integrity()
        if projected != self.state: _json(directory / 'state.json',self.state)
        return copy.deepcopy(self.state)

    def _request_state(self, request):
        arguments = {key:request[key] for key in ('run_id','change_id','summary','authority_mode','repositories','checks')}
        for key in ('upstream','delivery','maintenance'):
            if key in request: arguments[key]=request[key]
        state=dev.new_state(**arguments)
        if request.get('risk') is not None:
            dev._risk(request['risk'])
            if dev.RISK_ORDER[request['risk']['level']]<dev.RISK_ORDER[state['risk']['level']]:
                raise ValueError('intake risk cannot downgrade default authority-mode risk')
            if state['authority_mode']=='TECHNICAL_MAINTENANCE' and request['risk']['level']!='TRIVIAL':
                raise ValueError('maintenance must remain TRIVIAL')
            state['risk']=copy.deepcopy(request['risk'])
        if state['authority_mode']=='FEATURE_DELIVERY' and len(state['repositories'])>1:
            state['risk']['level']='HIGH_RISK'
            if 'CROSS_REPOSITORY' not in state['risk']['categories']: state['risk']['categories'].append('CROSS_REPOSITORY')
        return state

    @_operation
    def start(self, request):
        allowed = {'run_id','change_id','summary','authority_mode','repositories','checks','upstream','delivery','maintenance','repository_roots','risk'}
        if set(request)-allowed: raise ValueError('unsupported start fields: '+', '.join(sorted(set(request)-allowed)))
        state = self._request_state(request)
        request=copy.deepcopy(request)
        request['checks']=copy.deepcopy(state['checks'])
        for check in state['checks']: dev.identifier(check['name'])
        dev.validate_state(state,self.root,**self.context)
        identities = self._identities(state['repositories'],request.get('repository_roots',{}))
        directory = self.storage / 'runs' / state['run_id']
        if directory.exists(): raise ValueError('run identity already exists')
        self.state,self.frame_hash=state,None
        directory.mkdir(parents=True)
        request_ref = self._artifact('start-request.json',request)
        self.metadata=dict(schema_version=2,start_request=request_ref,repository_identities=identities,
                           review=None,verification=None,review_budget={key:0 for key in dev.REVIEW_LIMITS},
                           blocked_reason=None,fix_active=False,mutations=[],workflow={})
        self._bases()
        return self._save(state)

    @_operation
    def validate_authority(self):
        self.load()
        state=dev.advance(self.state,'AUTHORITY_VALIDATED',self.root,**self.context)
        self._scope_integrity()
        return self._save(state)

    @_operation
    def impact(self, value):
        self.load()
        ref=self._ingest(value,'impact','impact')
        return self._save(dev.analyze_impact(self.state,ref,self.root,**self.context))

    @_operation
    def impact_template(self):
        self.load()
        if self.state['authority_mode']!='FEATURE_DELIVERY' or self.state['lifecycle']!='AUTHORITY_VALIDATED':
            raise ValueError('impact template requires validated feature authority')
        upstream=dev.read_upstream(self.state['upstream'],self.root,**self.context)
        return dict(schema_version=2,change_id=self.state['change_id'],upstream_ref=self.state['upstream'],
                    repository_base_revisions=dev._bases(self.state['repositories']),
                    affected_repositories=copy.deepcopy(self.state['repositories']),
                    affected_components=[],affected_interfaces=[],affected_data=[],dependencies=[],constraints=[],
                    risk=copy.deepcopy(self.state['risk']),technical_unknowns=[dict(id='UNKNOWN-1',description='Complete engineering impact analysis',blocking=True)],
                    upstream_gaps=[],write_scope=dev._scope(self.state['repositories']),
                    knowledge_impact=copy.deepcopy(upstream['handoff']['knowledge_impact']))

    @_operation
    def plan(self, plan_path, tasks_path, decisions=(), revision=None):
        self.load()
        revision = revision or 'TECH-'+str(len(self.state['history'])+1)
        dev.identifier(revision)
        folder=self.run_directory/'planning'/revision
        binding=dict(run_id=self.state['run_id'],change_id=self.state['change_id'],upstream=self.state['upstream'],
                     engineering_impact=self.state['artifacts'].get('impact'),engineering_decisions=list(decisions),
                     repository_base_revisions=dev._bases(self.state['repositories']),write_scope=dev._scope(self.state['repositories']),
                     risk=self.state['risk'])
        header=b'<!-- Dev VNext exact technical binding: '+dev.semantic_bytes(binding)+b' -->\n\n'
        refs=[]
        for source,name in zip((plan_path,tasks_path),dev.PLANNING_NAMES):
            source=Path(source)
            if not source.is_absolute(): source=self.root/source
            target=folder/name
            expected=header+source.read_bytes()
            if target.exists():
                if target.read_bytes()!=expected: raise ValueError('immutable plan revision drift')
            else: _atomic(target,expected)
            refs.append(self.reference(target,revision))
        snapshot=dev.make_snapshot(self.state,self.root,revision=revision,decisions=list(decisions),plan=refs[0],tasks=refs[1],**self.context)
        ref=self._artifact('snapshots/'+revision+'.json',snapshot,revision)
        return self._save(dev.plan(self.state,ref,self.root,**self.context))

    @_operation
    def bind_technical_approval(self, receipt_ref):
        self.load()
        if self.state['gates'].get('technical_approval')==receipt_ref:
            raise ValueError('technical receipt replay is forbidden')
        return self._save(dev.bind_technical_approval(self.state,receipt_ref,self.root,**self.context))

    @_operation
    def implementation_ready(self):
        self.load()
        self._initial_base_guard()
        if self.state['authority_mode']=='TECHNICAL_MAINTENANCE':
            revision='TECH-'+str(len(self.state['history'])+1)
            snapshot=dev.maintenance_snapshot(self.state,self.root,revision=revision)
            ref=self._artifact('snapshots/'+revision+'.json',snapshot,revision)
            state=dev.prepare_maintenance(self.state,ref,self.root,current_base_revisions=self._bases())
        else:
            state=dev.advance(self.state,'IMPLEMENTATION_READY',self.root,current_base_revisions=self._bases(),**self.context)
            # Trusted callbacks may run arbitrary host code; observe Git again
            # before persisting an authorization they could have invalidated.
            self._bases()
        return self._save(state)

    @_operation
    def begin_implementation(self):
        self.load()
        return self._save(dev.advance(self.state,'IMPLEMENTING',self.root,**self.context))

    @_operation
    def authorize_write(self, repository_id, path):
        self.load()
        self._initial_base_guard()
        if self.metadata['blocked_reason']: raise ValueError(self.metadata['blocked_reason'])
        if self.metadata['review'] is not None and not self.metadata['fix_active']:
            raise ValueError('source mutation after review requires the single blocking fix wave')
        authorization=dev.authorize_source_mutation(self.state,self.root,repository_id,path,current_base_revisions=self._bases(),**self.context)
        self._physical_path(self._repository(repository_id),path)
        # Reobserve after all BA/Foundation/technical authenticators return.
        self._bases()
        return authorization

    @_operation
    def write_source(self, repository_id, path, content):
        self.authorize_write(repository_id,path)
        if self.state['lifecycle']=='IMPLEMENTATION_READY': self.begin_implementation()
        # Revalidate immediately before the filesystem mutation, after callbacks.
        self.authorize_write(repository_id,path)
        target=self._physical_path(self._repository(repository_id),path)
        _atomic(target,content.encode('utf-8') if isinstance(content,str) else content)
        self.metadata['mutations'].append(dict(repository_id=repository_id,source_path=path,content_sha256=hashlib.sha256(target.read_bytes()).hexdigest()))
        self.metadata['verification']=None
        self._save()
        return self.reference(target) if target.is_relative_to(self.root) else dict(repository_id=repository_id,path=path,sha256=hashlib.sha256(target.read_bytes()).hexdigest())

    @_operation
    def raise_gap(self, value):
        self.load()
        ref=self._ingest(value,'gaps','gap')
        state=dev.raise_gap(self.state,ref,self.root,**self.context)
        self.metadata.update(review=None,verification=None,fix_active=False)
        return self._save(state)

    @_operation
    def resume_gap(self, replacement_ref, resolution_ref):
        self.load(validate=False)
        state=dev.resume_gap(self.state,replacement_ref,resolution_ref,self.root,**self.context)
        self.metadata.update(review=None,verification=None,fix_active=False)
        return self._save(state)

    @_operation
    def escalate_risk(self, risk):
        self.load()
        state=dev.escalate_risk(self.state,risk)
        self.metadata.update(review=None,verification=None,fix_active=False)
        return self._save(state)

    @_operation
    def replan(self):
        self.load()
        return self._save(dev.replan(self.state,self.root,**self.context))

    @_operation
    def discover_maintenance_change(self, changes):
        self.load()
        if self.state['authority_mode']!='TECHNICAL_MAINTENANCE' or not changes:
            raise ValueError('maintenance discovery requires explicit discovered changes')
        state=copy.deepcopy(self.state)
        state['lifecycle']='BLOCKED'
        dev._event(self.state,state,'BLOCK')
        dev.validate_transition(self.state,state)
        self.metadata['blocked_reason']='BLOCKED: require FEATURE_DELIVERY authority; discovered '+', '.join(changes)
        return self._save(state)

    @_operation
    def record_review(self, evidence_refs, blocking_findings=(), *, kind='full', what_gap=None):
        self.load()
        if what_gap is not None: return self.raise_gap(what_gap)
        if self.state['lifecycle']!='IMPLEMENTING': raise ValueError('consolidated review requires IMPLEMENTING')
        if kind not in ('full','scoped'): raise ValueError('unsupported engineering review kind')
        budget=copy.deepcopy(self.metadata['review_budget'])
        key='full_reviews' if kind=='full' else 'scoped_rereviews'
        budget[key]+=1
        dev._budget(budget,completed=True)
        if kind=='scoped' and not self.metadata['fix_active']: raise ValueError('scoped rereview requires active blocking fix wave')
        revisions,_=self._outputs()
        if not evidence_refs: raise ValueError('exact consolidated review evidence required')
        for ref in evidence_refs: dev._ref(ref,self.root)
        review=dict(snapshot_sha256=self.state['artifacts']['snapshot']['sha256'],repository_revisions=revisions,
                    recorded_at=_stamp(),evidence_refs=list(evidence_refs),blocking_findings=list(blocking_findings),budget=budget)
        dev._check(review,dev.REVIEW)
        self.metadata.update(review=review,verification=None,review_budget=budget,fix_active=False)
        self._save()
        return copy.deepcopy(review)

    @_operation
    def begin_fix_wave(self):
        self.load()
        review=self.metadata['review']
        if self.state['lifecycle']!='IMPLEMENTING' or review is None or not review['blocking_findings']:
            raise ValueError('blocking fix wave requires consolidated blocking findings')
        budget=copy.deepcopy(self.metadata['review_budget'])
        budget['blocking_fix_waves']+=1
        dev._budget(budget,completed=True)
        self.metadata.update(review_budget=budget,fix_active=True,verification=None)
        return self._save()

    @_operation
    def complete_fix_wave(self, evidence_refs):
        """Seal exact fix evidence without requiring an optional scoped rereview."""
        self.load()
        if not self.metadata['fix_active']: raise ValueError('no active blocking fix wave')
        if not evidence_refs: raise ValueError('blocking fix resolution needs exact evidence')
        for ref in evidence_refs: dev._ref(ref,self.root)
        revisions,_=self._outputs()
        review=copy.deepcopy(self.metadata['review'])
        review.update(repository_revisions=revisions,recorded_at=_stamp(),blocking_findings=[],budget=copy.deepcopy(self.metadata['review_budget']))
        review['evidence_refs'].extend(evidence_refs)
        self.metadata.update(review=review,fix_active=False,verification=None)
        self._save()
        return copy.deepcopy(review)

    @_operation
    def verify(self):
        self.load()
        revisions,_=self._outputs()
        if self.state['lifecycle']=='IMPLEMENTING':
            if self.state['authority_mode']=='FEATURE_DELIVERY':
                review=self.metadata['review']
                if review is None or review['blocking_findings'] or self.metadata['fix_active']:
                    raise ValueError('fresh verification requires completed consolidated review/fix')
                if review['repository_revisions']!=revisions: raise ValueError('implementation changed after consolidated review')
                self._save(dev.advance(self.state,'ENGINEERING_REVIEW',self.root,**self.context))
            else:
                self.metadata['review']=dict(snapshot_sha256=self.state['artifacts']['snapshot']['sha256'],repository_revisions=revisions,
                    recorded_at=_stamp(),evidence_refs=[self.metadata['start_request']],blocking_findings=[],budget=copy.deepcopy(self.metadata['review_budget']))
            self._save(dev.advance(self.state,'VERIFYING',self.root,**self.context))
        if self.state['lifecycle']!='VERIFYING': raise ValueError('engineering checks require VERIFYING')
        if self.metadata['review']['repository_revisions']!=revisions: raise ValueError('review revision drift')
        results=[]
        for check in self.state['checks']:
            repository_id=check['repository_id']
            root=self._repository(repository_id)
            before=self._outputs()
            try:
                process=subprocess.run(check['command'],cwd=root,capture_output=True,text=True,encoding='utf-8',errors='replace',shell=False)
                exit_code,stdout,stderr=process.returncode,process.stdout,process.stderr
            except OSError as exc:
                exit_code,stdout,stderr=127,'',str(exc)
            if self._outputs()!=before: raise ValueError('repository-native check mutated implementation revision/scope')
            status='PASS' if exit_code==0 else 'FAIL'
            implementation_revision=revisions[repository_id]
            executions=[dict(repository_id=repository_id,implementation_revision=implementation_revision,
                argv=check['command'],exit_code=exit_code,stdout=stdout,stderr=stderr)]
            evidence=dict(artifact_class='EVIDENCE',name=check['name'],category=check['category'],command=check['command'],
                          repository_id=repository_id,implementation_revision=implementation_revision,
                          status=status,exit_code=exit_code,
                          snapshot_sha256=self.state['artifacts']['snapshot']['sha256'],repository_revisions=revisions,
                          recorded_at=_stamp(),executions=executions)
            ref=self._artifact('evidence/checks/'+check['name']+'-'+str(len(list((self.run_directory/'evidence/checks').glob('*.json'))))+'.json',evidence)
            results.append({**check,'exit_code':exit_code,'status':status,'evidence_ref':ref})
        verification=dict(snapshot_sha256=self.state['artifacts']['snapshot']['sha256'],repository_revisions=revisions,recorded_at=_stamp(),checks=results)
        self.metadata['verification']=verification
        self._save()
        return copy.deepcopy(verification)

    @_operation
    def finalize(self, coverage, known_risks=()):
        self.load()
        revisions,paths=self._outputs()
        if self.metadata['review'] is None or self.metadata['verification'] is None:
            raise ValueError('finalization requires fresh runtime review and process evidence')
        implementation=[]
        for repository_id,revision in revisions.items():
            evidence=dict(artifact_class='EVIDENCE',repository_id=repository_id,revision=revision,
                          base_revision=dev._bases(self.state['repositories'])[repository_id],changed_paths=paths[repository_id])
            ref=self._artifact('evidence/implementation/'+repository_id+'-'+revision+'.json',evidence,revision)
            implementation.append(dict(repository_id=repository_id,revision=revision,changed_paths=paths[repository_id],evidence_refs=[ref]))
        handoff=dev.make_handoff(self.state,self.root,repository_revisions=revisions,current_base_revisions=self._bases(),
            implementation=implementation,coverage=coverage,review=self.metadata['review'],verification=self.metadata['verification'],known_risks=list(known_risks),**self.context)
        dev.validate_handoff(handoff,self.root,current_base_revisions=self._bases(),**self.context)
        if self._outputs()[0]!=revisions: raise ValueError('implementation revision drift during handoff validation')
        self._artifact('dev-handoff.json',handoff,'HANDOFF-'+str(len(self.state['history'])+1))
        self._save(handoff['run_state'])
        return handoff

    @_operation
    def status(self):
        state=self.load()
        return dict(mode='VNEXT',vnext_authority=state['lifecycle']!='INTAKE',state=state,
                    delivery_manifest='DEFERRED_NON_AUTHORITATIVE',review_budget=copy.deepcopy(self.metadata['review_budget']),
                    blocked_reason=self.metadata['blocked_reason'])

    @_operation
    def technical_gate_required(self):
        self.load()
        snapshot=dev.validate_snapshot(self.state['artifacts'].get('snapshot'),self.root,self.state,**self.context)
        return dev._gate_required(snapshot,self.root,self.state,**self.context)

    @_operation
    def record_workflow(self, metadata):
        """Workflow transport identity is evidence only and never a gate."""
        self.load()
        if not isinstance(metadata,dict): raise ValueError('workflow identity metadata required')
        dev.reject_secrets(metadata)
        metadata=copy.deepcopy(metadata)
        if 'workflow_state_ref' in metadata:
            workflow_id=metadata.get('workflow_run_id')
            dev.identifier(workflow_id)
            source=metadata['workflow_state_ref']
            source={**source,'revision':source.get('revision',workflow_id)}
            document=dev._data(source,self.root)
            metadata['workflow_source_path']=source['path']
            metadata['workflow_source_sha256']=source['sha256']
            metadata['workflow_state_ref']=self._artifact('evidence/workflow/'+workflow_id+'-'+source['sha256']+'.json',document,source['revision'])
        for ref in dev._all_refs(metadata): dev._ref(ref,self.root)
        self.metadata['workflow']=copy.deepcopy(metadata)
        return self._save()
