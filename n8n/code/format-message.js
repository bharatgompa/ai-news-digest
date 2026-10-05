// Turn Claude's JSON into Telegram HTML messages (max ~4000 chars each).
const res = $input.first().json;
if (res.stop_reason === "refusal") throw new Error("Claude declined the request");
const text = (res.content || []).find((b) => b.type === "text")?.text;
if (!text) throw new Error("No text in Claude response: " + JSON.stringify(res).slice(0, 500));
const digest = JSON.parse(text);

const items = $("Filter & Build Prompt").first().json.items;
const byId = Object.fromEntries(items.map((it) => [it.id, it]));
const esc = (s) => String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
const mark = { 5: "🔥", 4: "⭐" };
const date = new Date(Date.now() + 5.5 * 3600 * 1000).toISOString().slice(0, 10); // IST

const blocks = [`<b>🗞 Daily Digest — ${date}</b>\n<i>${esc(digest.headline)}</i>`];
for (const section of digest.sections) {
  const stories = section.stories
    .filter((s) => byId[s.item_id])
    .sort((a, b) => b.importance - a.importance)
    .map((s) => `${mark[s.importance] || "•"} <a href="${esc(byId[s.item_id].url)}">${esc(s.title)}</a>\n${esc(s.summary)}\n<i>↳ ${esc(s.why_it_matters)}</i>`);
  if (stories.length) blocks.push(`<b>${esc(section.title)}</b>\n\n` + stories.join("\n\n"));
}

const messages = [];
let cur = "";
for (const b of blocks) {
  if (cur && cur.length + b.length + 2 > 4000) { messages.push(cur); cur = ""; }
  cur += (cur ? "\n\n" : "") + b;
}
if (cur) messages.push(cur);
return messages.map((m) => ({ json: { text: m } }));
