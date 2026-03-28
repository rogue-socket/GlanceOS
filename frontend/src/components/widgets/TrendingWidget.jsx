import WidgetCard from '../WidgetCard';

function formatStars(n) {
  if (!n) return '0';
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`;
  return String(n);
}

const LANG_COLORS = {
  JavaScript: '#f1e05a',
  TypeScript: '#3178c6',
  Python: '#3572A5',
  Rust: '#dea584',
  Go: '#00ADD8',
  Zig: '#ec915c',
  Java: '#b07219',
  'C++': '#f34b7d',
  C: '#555555',
  Ruby: '#701516',
  Swift: '#F05138',
  Kotlin: '#A97BFF',
};

export default function TrendingWidget({ data }) {
  if (!data) {
    return (
      <WidgetCard title="Trending" icon="trending">
        <div className="flex items-center justify-center h-full text-glance-muted text-sm">
          Waiting for data…
        </div>
      </WidgetCard>
    );
  }

  const repos = data.repos || [];
  const sourceTone = (data.source || '').includes('github') ? 'text-glance-success' : 'text-glance-warning';

  return (
    <WidgetCard title={`Trending · ${data.since || 'daily'}`} icon="trending">
      <div className="flex flex-col gap-1 pt-1">
        <div className="text-[10px] text-glance-muted/70 uppercase tracking-[0.12em] flex items-center gap-1.5">
          <span aria-hidden="true">◉</span>
          <span className={sourceTone}>Source: {data.source || 'live'}</span>
        </div>
        {repos.length === 0 && (
          <div className="text-sm text-glance-muted text-center">
            {data.error || 'No trending repositories right now'}
          </div>
        )}
        {repos.map((repo, i) => (
          <a
            key={repo.name || i}
            href={repo.url || `https://github.com/${repo.name}`}
            target="_blank"
            rel="noreferrer noopener"
            className="flex items-start gap-2 py-1.5 border-b border-glance-border/20 last:border-0 hover:bg-glance-accent-dim/30 -mx-1 px-1 rounded transition-colors"
          >
            <span className="text-glance-accent/40 text-[10px] font-mono mt-0.5 shrink-0">
              {String(i + 1).padStart(2, '0')}
            </span>
            <div className="min-w-0 flex-1">
              <div className="text-xs text-glance-accent font-semibold truncate flex items-center gap-1">
                <span aria-hidden="true">🔗</span>
                <span>{repo.name}</span>
              </div>
              {repo.description && (
                <div className="text-[10px] text-glance-muted leading-snug line-clamp-1 mt-0.5">
                  {repo.description}
                </div>
              )}
              <div className="flex items-center gap-3 mt-1">
                {repo.language && (
                  <span className="flex items-center gap-1 text-[10px] text-glance-muted">
                    <span
                      className="w-2 h-2 rounded-full inline-block"
                      style={{ background: LANG_COLORS[repo.language] || '#8b8b8b' }}
                    />
                    {repo.language}
                  </span>
                )}
                <span className="text-[10px] text-glance-muted"><span aria-hidden="true">★</span> {formatStars(repo.stars)}</span>
                {repo.today_stars > 0 && (
                  <span className="text-[10px] text-glance-success font-medium">
                    <span aria-hidden="true">▲</span> +{formatStars(repo.today_stars)} today
                  </span>
                )}
              </div>
            </div>
          </a>
        ))}
      </div>
    </WidgetCard>
  );
}
