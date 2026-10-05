// Feed list — one output item per feed. The RSS Read node runs once per item.
// YouTube channel feed: https://www.youtube.com/feeds/videos.xml?channel_id=<ID>
const feeds = [
  "https://hnrss.org/frontpage?points=150",
  "https://techcrunch.com/category/artificial-intelligence/feed/",
  "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
  "https://www.technologyreview.com/topic/artificial-intelligence/feed",
  "https://openai.com/news/rss.xml",
  "https://feed.infoq.com/",
  "https://blog.pragmaticengineer.com/rss/",
  "https://inc42.com/feed/",
  "https://economictimes.indiatimes.com/tech/rssfeeds/13357270.cms",
  "https://www.livemint.com/rss/markets",
  "https://www.youtube.com/feeds/videos.xml?channel_id=UCsBjURrPoezykLs9EqgamOA",
  "https://www.youtube.com/feeds/videos.xml?channel_id=UCZgt6AzoyjslHTC9dz0UoTw",
];
return feeds.map((url) => ({ json: { url } }));
