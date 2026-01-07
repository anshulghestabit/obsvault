const fs = require("fs");
const path = require("path");

const inputPath = path.join(__dirname, "../frankenstein.txt");
const outputPath = path.join(__dirname, "../corpus.txt");
const text = fs.readFileSync(inputPath, "utf-8");
const multiplied = text.repeat(4);
fs.writeFileSync(outputPath, multiplied);

console.log("done ");
