const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const dataDir = path.join(root, "data");
const coursesDir = path.join(dataDir, "courses");
const glossaryPath = path.join(dataDir, "glossary.json");
const indexPath = path.join(dataDir, "course-index.js");

function json(value) {
  return JSON.stringify(value);
}

function jsString(value) {
  return JSON.stringify(String(value));
}

function courseSummary(course) {
  const { terms, figures, ...summary } = course;
  return {
    ...summary,
    meta: {
      ...(course.meta || {}),
      totalTerms: course.meta?.totalTerms || terms?.length || 0,
      totalFigures: course.meta?.totalFigures || figures?.length || 0,
    },
  };
}

function main() {
  const library = JSON.parse(fs.readFileSync(glossaryPath, "utf8"));
  fs.mkdirSync(coursesDir, { recursive: true });

  const index = {
    schemaVersion: library.schemaVersion,
    meta: library.meta || {},
    courses: (library.courses || []).map(courseSummary),
  };

  fs.writeFileSync(indexPath, `window.MED_GLOSSARY_INDEX=${json(index)};\n`, "utf8");

  for (const course of library.courses || []) {
    const outputPath = path.join(coursesDir, `${course.id}.js`);
    const source = [
      "window.MED_GLOSSARY_COURSES=window.MED_GLOSSARY_COURSES||{};",
      `window.MED_GLOSSARY_COURSES[${jsString(course.id)}]=${json(course)};`,
      "",
    ].join("");
    fs.writeFileSync(outputPath, source, "utf8");
  }
}

main();
