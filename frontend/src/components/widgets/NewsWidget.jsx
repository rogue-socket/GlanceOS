import WidgetCard from '../WidgetCard';

function timeAgo(dateStr) {
  if (!dateStr) return '';
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

export default function NewsWidget({ data }) {
  if (!data) {
    return (
      <WidgetCard title="News" icon="news">
        <div className="flex items-center justify-center h-full text-glance-muted text-sm">
          Waiting for data…
        </div>
      </WidgetCard>
    );
  }

  const articles = data.articles || [];
  const isUnavailable = data.status === 'unavailable';

  const feedSource = data.source || 'news';

  return (
    <WidgetCard title={`News · ${data.category || 'tech'}`} icon="news">
      <div className="flex flex-col gap-1.5 pt-1">
        <div className="text-[10px] uppercase tracking-[0.12em] text-glance-muted/70">
          source: {feedSource}
        </div>
        {isUnavailable && (
          <div className="text-xs text-glance-muted bg-glance-accent-dim/20 border border-glance-border/40 rounded-md px-2 py-2">
            {data.reason || 'Live news unavailable right now'}
          </div>
        )}
        {articles.length === 0 && (
          <div className="text-sm text-glance-muted text-center">No articles</div>
        )}
        {articles.map((article, i) => {
          const rowContent = (
            <>
              <span className="text-glance-accent/60 text-[10px] font-mono mt-0.5 shrink-0">
                {String(i + 1).padStart(2, '0')}
              </span>
              <div className="min-w-0 flex-1">
                <div className="text-xs text-glance-text leading-snug line-clamp-2 group-hover:text-glance-accent transition-colors">
                  {article.crux || article.title}
                </div>
                {article.summary && (
                  <div className="text-[11px] text-glance-text/85 leading-snug line-clamp-3 mt-0.5">
                    {article.summary}
                  </div>
                )}
                {article.crux && article.title && article.crux !== article.title && (
                  <div className="text-[10px] text-glance-muted/80 leading-snug line-clamp-1 mt-0.5">
                    {article.title}
                  </div>
                )}
                <div className="flex items-center gap-2 mt-0.5">
                  <span className="text-[10px] text-glance-muted truncate">
                    {article.source}
                  </span>
                  {article.published && (
                    <span className="text-[10px] text-glance-muted/60">
                      {timeAgo(article.published)}
                    </span>
                  )}
                  {article.url && (
                    <span className="text-[10px] text-glance-accent/80 opacity-0 group-hover:opacity-100 transition-opacity">
                      open
                    </span>
                  )}
                </div>
              </div>
            </>
          );

          if (article.url) {
            return (
              <a
                key={i}
                href={article.url}
                target="_blank"
                rel="noreferrer"
                className="group flex gap-2 items-start py-1.5 border-b border-glance-border/20 last:border-0 hover:bg-glance-accent-dim/30 -mx-1 px-1 rounded transition-colors"
              >
                {rowContent}
              </a>
            );
          }

          return (
            <div
              key={i}
              className="group flex gap-2 items-start py-1.5 border-b border-glance-border/20 last:border-0 -mx-1 px-1 rounded"
            >
              {rowContent}
            </div>
          );
        })}
        {data.llm_enriched && (
          <div className="text-[9px] text-glance-muted/60 text-center mt-1">
            content summarized by llm
          </div>
        )}
      </div>
    </WidgetCard>
  );
}
