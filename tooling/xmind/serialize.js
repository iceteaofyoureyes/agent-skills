"use strict";

const fs = require("fs");
const path = require("path");
const { Workbook, Topic, Zipper } = require("xmind");

const EXPECTED_VERSION = "2.2.33";

function addTopic(topicApi, parentId, node) {
  if (
    !node || typeof node.title !== "string" || !Array.isArray(node.children) ||
    Object.keys(node).some((key) => !["title", "children", "component_id", "custom_id"].includes(key))
  ) {
    throw new Error("invalid semantic projection topic");
  }
  const component = { title: node.title };
  if (node.component_id !== undefined) {
    if (typeof node.component_id !== "string" || !/^[0-9a-f]{8}-[0-9a-f]{4}-5[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/.test(node.component_id)) {
      throw new Error("invalid deterministic XMind component ID");
    }
    component.id = node.component_id;
  }
  if (node.custom_id !== undefined) {
    if (typeof node.custom_id !== "string" || !node.custom_id) throw new Error("invalid custom XMind component ID");
    component.customId = node.custom_id;
  }
  topicApi.on(parentId).add(component);
  const topicId = topicApi.cid();
  for (const child of node.children) addTopic(topicApi, topicId, child);
}

async function main() {
  const sdk = require("xmind/package.json");
  if (sdk.version !== EXPECTED_VERSION) throw new Error(`unexpected XMind SDK version: ${sdk.version}`);
  const outputDir = path.resolve(process.argv[2]);
  const filename = process.argv[3];
  if (!/^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$/.test(filename)) throw new Error("unsafe output filename");
  const model = JSON.parse(fs.readFileSync(0, "utf8"));
  if (typeof model.sheet_title !== "string" || typeof model.root_title !== "string" || !Array.isArray(model.children)) {
    throw new Error("invalid semantic projection model");
  }

  const workbook = new Workbook();
  const sheet = workbook.createSheet(model.sheet_title, model.root_title);
  const topicApi = new Topic({ sheet });
  topicApi.rootTopic.changeStructureClass("org.xmind.ui.logic.right");
  for (const child of model.children) addTopic(topicApi, topicApi.rootTopicId, child);
  const validation = workbook.validate();
  if (!validation.status) throw new Error("XMind SDK rejected the workbook model");
  const saved = await new Zipper({ path: outputDir, workbook, filename }).save();
  if (!saved) throw new Error("XMind SDK failed to save the workbook");
}

main().catch((error) => {
  process.stderr.write(`${error.message}\n`);
  process.exitCode = 1;
});
