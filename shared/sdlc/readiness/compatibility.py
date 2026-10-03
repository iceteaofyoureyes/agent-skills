"""Doctor compatibility is scoped to package diagnostics, never approval."""
from types import MappingProxyType

DOCTOR_PACKAGE_COMPATIBILITY = MappingProxyType({'READY':True,'DEGRADED':False,'FAIL':False})


def normalize_doctor(status):
    if not isinstance(status,str) or status not in DOCTOR_PACKAGE_COMPATIBILITY:
        raise ValueError('unsupported Doctor status')
    return {'readiness':'PACKAGE_READY','ready':DOCTOR_PACKAGE_COMPATIBILITY[status],
            'doctor_status':status,'human_approval':False,'feature_ready':False}
