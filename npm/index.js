"use strict";

const { spawn } = require("child_process");

function launchWaveCraft(options = {}) {
  const args = [];
  if (options.port) args.push("--port", String(options.port));
  if (options.noOpen) args.push("--no-open");
  return spawn(process.execPath, [require.resolve("./bin/wavecraft.js"), ...args], {
    stdio: "inherit",
  });
}

module.exports = { launchWaveCraft };
