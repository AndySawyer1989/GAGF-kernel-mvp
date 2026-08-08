export type GovernanceInterventionPlanItem = {
  interventionId: string;
  interventionType: string;
  title: string;
  constraintCategory: string;
  priority: string;
  rank: number;
  valueScore: number;
  expectedFrictionReduction: number;
  evidenceConfidence: number;
  affectedWorkReach: number;
  implementationBurden: number;
  reversibility: number;
  rationale: string[];
  isTopIntervention: boolean;
};

type GovernanceInterventionPlanProps = {
  items: GovernanceInterventionPlanItem[];
  governanceDebtScore: number;
  planHash: string | null;
  schemaVersion: string | null;
};

function humanize(value: string): string {
  return value
    .replaceAll("_", " ")
    .replaceAll("-", " ")
    .replace(/\b\w/g, (character) =>
      character.toUpperCase()
    );
}

function percent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function score(value: number): string {
  return value.toFixed(1);
}

function metricWidth(value: number): string {
  const normalized = Math.max(
    0,
    Math.min(value, 1)
  );

  return `${normalized * 100}%`;
}

export function GovernanceInterventionPlan({
  items,
  governanceDebtScore,
  planHash,
  schemaVersion
}: GovernanceInterventionPlanProps) {
  const orderedItems = [...items].sort(
    (left, right) => left.rank - right.rank
  );

  const topIntervention =
    orderedItems.find(
      (item) => item.isTopIntervention
    ) ??
    orderedItems[0] ??
    null;

  return (
    <section
      className="panel governance-intervention-panel"
      aria-labelledby="governance-intervention-plan-title"
    >
      <div className="panel-header governance-intervention-header">
        <div>
          <p className="panel-kicker">
            Governed intervention guidance
          </p>

          <h2 id="governance-intervention-plan-title">
            Ranked intervention plan
          </h2>

          <p className="governance-intervention-intro">
            Deterministic intervention candidates produced by
            the governed assessment engine.
          </p>
        </div>

        <div className="governance-intervention-debt">
          <span>Governance debt</span>
          <strong>
            {score(governanceDebtScore)}
          </strong>
        </div>
      </div>

      {orderedItems.length === 0 ? (
        <div className="governance-intervention-empty">
          <strong>
            No ranked interventions are available.
          </strong>

          <p>
            The governed intervention artifact did not contain
            intervention candidates.
          </p>
        </div>
      ) : (
        <>
          {topIntervention ? (
            <div className="governance-intervention-top">
              <div className="governance-intervention-top-copy">
                <span className="governance-intervention-eyebrow">
                  Highest-ranked intervention
                </span>

                <strong>
                  {topIntervention.title}
                </strong>

                <span>
                  {humanize(
                    topIntervention.constraintCategory
                  )}
                </span>
              </div>

              <div className="governance-intervention-top-score">
                <span>Value score</span>

                <strong>
                  {score(
                    topIntervention.valueScore
                  )}
                </strong>
              </div>
            </div>
          ) : null}

          <div
            className="governance-intervention-list"
            aria-label="Ranked governance interventions"
          >
            {orderedItems.map((item) => (
              <article
                className={[
                  "governance-intervention-card",
                  item.isTopIntervention
                    ? "governance-intervention-card-top"
                    : ""
                ]
                  .filter(Boolean)
                  .join(" ")}
                key={item.interventionId}
              >
                <div className="governance-intervention-card-heading">
                  <div className="governance-intervention-rank">
                    <span>Rank</span>
                    <strong>{item.rank}</strong>
                  </div>

                  <div className="governance-intervention-title-group">
                    <div className="governance-intervention-badges">
                      <span
                        className={[
                          "governance-intervention-priority",
                          `governance-intervention-priority-${item.priority}`
                        ].join(" ")}
                      >
                        {humanize(item.priority)}
                      </span>

                      <span className="governance-intervention-type">
                        {humanize(item.interventionType)}
                      </span>
                    </div>

                    <h3>{item.title}</h3>

                    <p>
                      Constraint:{" "}
                      <strong>
                        {humanize(
                          item.constraintCategory
                        )}
                      </strong>
                    </p>
                  </div>

                  <div className="governance-intervention-value">
                    <span>Value</span>
                    <strong>
                      {score(item.valueScore)}
                    </strong>
                  </div>
                </div>

                <div className="governance-intervention-metrics">
                  <InterventionMetric
                    label="Expected friction reduction"
                    value={
                      item.expectedFrictionReduction
                    }
                  />

                  <InterventionMetric
                    label="Evidence confidence"
                    value={item.evidenceConfidence}
                  />

                  <InterventionMetric
                    label="Affected-work reach"
                    value={item.affectedWorkReach}
                  />

                  <InterventionMetric
                    label="Implementation burden"
                    value={item.implementationBurden}
                  />

                  <InterventionMetric
                    label="Reversibility"
                    value={item.reversibility}
                  />
                </div>

                <div className="governance-intervention-rationale">
                  <strong>
                    Evidence-backed rationale
                  </strong>

                  {item.rationale.length > 0 ? (
                    <ul>
                      {item.rationale.map(
                        (
                          rationale,
                          rationaleIndex
                        ) => (
                          <li
                            key={`${item.interventionId}-${rationaleIndex}`}
                          >
                            {rationale}
                          </li>
                        )
                      )}
                    </ul>
                  ) : (
                    <p>
                      No additional rationale was supplied by
                      the governed artifact.
                    </p>
                  )}
                </div>
              </article>
            ))}
          </div>
        </>
      )}

      <footer className="governance-intervention-footer">
        <div>
          <strong>
            Interpretation boundary
          </strong>

          <p>
            Rank represents governed intervention priority.
            It does not establish execution order, ownership,
            dependencies, approval, or implementation schedule.
          </p>
        </div>

        <div className="governance-intervention-provenance">
          {schemaVersion ? (
            <span>
              Schema{" "}
              <strong>{schemaVersion}</strong>
            </span>
          ) : null}

          {planHash ? (
            <span title={planHash}>
              Plan hash{" "}
              <code>
                {planHash.slice(0, 12)}…
              </code>
            </span>
          ) : null}
        </div>
      </footer>
    </section>
  );
}

function InterventionMetric({
  label,
  value
}: {
  label: string;
  value: number;
}) {
  return (
    <div className="governance-intervention-metric">
      <div className="governance-intervention-metric-heading">
        <span>{label}</span>
        <strong>{percent(value)}</strong>
      </div>

      <div
        className="governance-intervention-meter"
        aria-hidden="true"
      >
        <span
          style={{
            width: metricWidth(value)
          }}
        />
      </div>
    </div>
  );
}
