export type GovernanceFrictionMapItem = {
  category: string;
  eventCount: number;
  uniqueWorkItemCount: number;
  firstOccurredAt: string;
  lastOccurredAt: string;
  weight: number;
  frictionScore: number;
  eventShare: number;
  band: string;
  isDominant: boolean;
};

type GovernanceFrictionMapProps = {
  items: GovernanceFrictionMapItem[];
  totalFrictionScore: number;
  recognizedEventCount: number;
  uniqueWorkItemCount: number;
  dominantConstraint: string;
};

type MapPosition = {
  x: number;
  y: number;
};

const MAP_WIDTH = 900;
const MAP_HEIGHT = 540;
const MAP_CENTER_X = MAP_WIDTH / 2;
const MAP_CENTER_Y = MAP_HEIGHT / 2;
const MAP_RADIUS_X = 330;
const MAP_RADIUS_Y = 190;

function categoryLabel(value: string): string {
  return value
    .toLowerCase()
    .split("_")
    .map((word) =>
      word.length > 0
        ? word[0].toUpperCase() + word.slice(1)
        : word
    )
    .join(" ");
}

function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function formatDate(value: string): string {
  const parsed = new Date(value);

  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric"
  }).format(parsed);
}

function bandClassName(band: string): string {
  const normalized = band.toLowerCase();

  if (
    normalized === "low" ||
    normalized === "moderate" ||
    normalized === "high" ||
    normalized === "severe"
  ) {
    return `friction-band-${normalized}`;
  }

  return "friction-band-unknown";
}

function mapPosition(
  index: number,
  itemCount: number
): MapPosition {
  if (itemCount <= 1) {
    return {
      x: MAP_CENTER_X,
      y: 105
    };
  }

  const angle =
    -Math.PI / 2 +
    (index * Math.PI * 2) / itemCount;

  return {
    x:
      MAP_CENTER_X +
      Math.cos(angle) * MAP_RADIUS_X,
    y:
      MAP_CENTER_Y +
      Math.sin(angle) * MAP_RADIUS_Y
  };
}

export function GovernanceFrictionMap({
  items,
  totalFrictionScore,
  recognizedEventCount,
  uniqueWorkItemCount,
  dominantConstraint
}: GovernanceFrictionMapProps) {
  const orderedItems = [...items].sort(
    (left, right) =>
      right.frictionScore - left.frictionScore ||
      left.category.localeCompare(right.category)
  );

  const dominantLabel =
    dominantConstraint.length > 0
      ? categoryLabel(dominantConstraint)
      : "Not identified";

  return (
    <section
      className="panel governance-friction-map-panel"
      aria-labelledby="governance-friction-map-title"
    >
      <div className="panel-header friction-map-header">
        <div>
          <p className="panel-kicker">
            Governed constraint topology
          </p>

          <h2 id="governance-friction-map-title">
            Governance friction map
          </h2>

          <p className="friction-map-description">
            Each connection represents a measured
            constraint category contributing to the
            assessment&apos;s total governed friction.
          </p>
        </div>

        <span className="status-badge status-warning">
          <span
            className="status-dot"
            aria-hidden="true"
          />

          Dominant: {dominantLabel}
        </span>
      </div>

      {orderedItems.length === 0 ? (
        <div className="friction-map-empty">
          <h3>No measurable constraint topology</h3>

          <p>
            The persisted friction-summary artifact does
            not contain recognized constraint
            aggregations for this assessment.
          </p>
        </div>
      ) : (
        <>
          <div className="friction-map-summary-grid">
            <div>
              <span>Total friction</span>
              <strong>
                {totalFrictionScore.toFixed(1)}
              </strong>
            </div>

            <div>
              <span>Recognized events</span>
              <strong>{recognizedEventCount}</strong>
            </div>

            <div>
              <span>Affected work items</span>
              <strong>{uniqueWorkItemCount}</strong>
            </div>

            <div>
              <span>Constraint categories</span>
              <strong>{orderedItems.length}</strong>
            </div>
          </div>

          <div className="friction-map-visual-shell">
            <svg
              className="friction-map-svg"
              viewBox={`0 0 ${MAP_WIDTH} ${MAP_HEIGHT}`}
              role="img"
              aria-labelledby="
                friction-map-svg-title
                friction-map-svg-description
              "
            >
              <title id="friction-map-svg-title">
                Constraint contribution map
              </title>

              <desc id="friction-map-svg-description">
                A central governed assessment node is
                connected to each measured constraint
                category. Larger nodes indicate higher
                friction scores.
              </desc>

              <g className="friction-map-edges">
                {orderedItems.map((item, index) => {
                  const position = mapPosition(
                    index,
                    orderedItems.length
                  );

                  return (
                    <line
                      className={
                        item.isDominant
                          ? "friction-map-edge friction-map-edge-dominant"
                          : "friction-map-edge"
                      }
                      key={`edge-${item.category}`}
                      x1={MAP_CENTER_X}
                      y1={MAP_CENTER_Y}
                      x2={position.x}
                      y2={position.y}
                    />
                  );
                })}
              </g>

              <g
                className="friction-map-core-node"
                transform={
                  `translate(${MAP_CENTER_X}, ${MAP_CENTER_Y})`
                }
              >
                <circle r="76" />

                <text
                  className="friction-map-core-label"
                  textAnchor="middle"
                  y="-14"
                >
                  Governed
                </text>

                <text
                  className="friction-map-core-label"
                  textAnchor="middle"
                  y="8"
                >
                  assessment
                </text>

                <text
                  className="friction-map-core-score"
                  textAnchor="middle"
                  y="39"
                >
                  {totalFrictionScore.toFixed(1)}
                </text>
              </g>

              {orderedItems.map((item, index) => {
                const position = mapPosition(
                  index,
                  orderedItems.length
                );

                const radius = Math.min(
                  58,
                  34 + item.frictionScore * 1.4
                );

                const label = categoryLabel(
                  item.category
                );

                return (
                  <g
                    className={
                      item.isDominant
                        ? `friction-map-node ${bandClassName(
                            item.band
                          )} friction-map-node-dominant`
                        : `friction-map-node ${bandClassName(
                            item.band
                          )}`
                    }
                    key={item.category}
                    transform={
                      `translate(${position.x}, ${position.y})`
                    }
                  >
                    <circle r={radius} />

                    <text
                      className="friction-map-node-label"
                      textAnchor="middle"
                      y="-8"
                    >
                      {label.length > 19
                        ? `${label.slice(0, 18)}…`
                        : label}
                    </text>

                    <text
                      className="friction-map-node-score"
                      textAnchor="middle"
                      y="18"
                    >
                      {item.frictionScore.toFixed(1)}
                    </text>
                  </g>
                );
              })}
            </svg>
          </div>

          <div
            className="friction-map-detail-grid"
            aria-label="Constraint contribution details"
          >
            {orderedItems.map((item) => (
              <article
                className={
                  item.isDominant
                    ? "friction-map-detail-card friction-map-detail-card-dominant"
                    : "friction-map-detail-card"
                }
                key={item.category}
              >
                <div className="friction-map-detail-heading">
                  <div>
                    <p className="friction-map-category">
                      {categoryLabel(item.category)}
                    </p>

                    {item.isDominant ? (
                      <span className="friction-map-dominant-label">
                        Dominant constraint
                      </span>
                    ) : null}
                  </div>

                  <span
                    className={
                      `friction-band-badge ${bandClassName(
                        item.band
                      )}`
                    }
                  >
                    {item.band}
                  </span>
                </div>

                <dl className="friction-map-detail-metrics">
                  <div>
                    <dt>Friction score</dt>
                    <dd>
                      {item.frictionScore.toFixed(1)}
                    </dd>
                  </div>

                  <div>
                    <dt>Event share</dt>
                    <dd>
                      {formatPercent(item.eventShare)}
                    </dd>
                  </div>

                  <div>
                    <dt>Events</dt>
                    <dd>{item.eventCount}</dd>
                  </div>

                  <div>
                    <dt>Work items</dt>
                    <dd>{item.uniqueWorkItemCount}</dd>
                  </div>

                  <div>
                    <dt>Weight</dt>
                    <dd>{item.weight.toFixed(1)}</dd>
                  </div>
                </dl>

                <p className="friction-map-time-range">
                  Observed {formatDate(item.firstOccurredAt)}
                  {" – "}
                  {formatDate(item.lastOccurredAt)}
                </p>
              </article>
            ))}
          </div>

          <footer className="friction-map-footer">
            <p>
              Connections show measured contribution to
              assessment friction. They do not assert
              workflow sequence, causality, or authority
              relationships not present in the governed
              artifact.
            </p>
          </footer>
        </>
      )}
    </section>
  );
}
