export type GovernanceRoadmapItem = {
  roadmapItemId: string;
  interventionId: string;
  interventionType: string;
  title: string;
  horizon: string;
  sequence: number;
  ownerRole: string;
  measurableOutcome: string;
  valueScore: number;
  implementationBurden: number;
  dependencyIds: string[];
  status: string;
};

export type GovernanceRoadmapPhase = {
  horizon: string;
  objective: string;
  itemCount: number;
  items: GovernanceRoadmapItem[];
};

type GovernanceRoadmapProps = {
  phases: GovernanceRoadmapPhase[];
  totalItems: number;
  interventionPlanHash: string | null;
  roadmapHash: string | null;
  schemaVersion: string | null;
};

function humanize(value: string): string {
  return value
    .replace(/[-_]+/g, " ")
    .replace(/\b\w/g, (character) =>
      character.toUpperCase()
    );
}

function score(value: number): string {
  return value.toFixed(2);
}

function percent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function phaseOrder(horizon: string): number {
  if (horizon === "30-day") {
    return 30;
  }

  if (horizon === "60-day") {
    return 60;
  }

  if (horizon === "90-day") {
    return 90;
  }

  return Number.MAX_SAFE_INTEGER;
}

export function GovernanceRoadmap({
  phases,
  totalItems,
  interventionPlanHash,
  roadmapHash,
  schemaVersion
}: GovernanceRoadmapProps) {
  const orderedPhases = [...phases].sort(
    (left, right) =>
      phaseOrder(left.horizon) -
      phaseOrder(right.horizon)
  );

  return (
    <section className="assessment-panel governance-roadmap-panel">
      <div className="assessment-panel-heading governance-roadmap-header">
        <div>
          <p className="assessment-eyebrow">
            Governed execution planning
          </p>

          <h2>30 / 60 / 90-Day Roadmap</h2>

          <p className="governance-roadmap-intro">
            The roadmap projects the governed execution
            structure produced by the assessment engine.
            Horizons, sequence, ownership, dependencies,
            outcomes, and status are authoritative artifact
            values rather than frontend estimates.
          </p>
        </div>

        <div className="governance-roadmap-total">
          <span>Roadmap items</span>
          <strong>{totalItems}</strong>
        </div>
      </div>

      <div className="governance-roadmap-phases">
        {orderedPhases.map((phase) => {
          const orderedItems = [...phase.items].sort(
            (left, right) =>
              left.sequence - right.sequence
          );

          return (
            <section
              className="governance-roadmap-phase"
              key={phase.horizon}
            >
              <header className="governance-roadmap-phase-header">
                <div>
                  <p className="governance-roadmap-horizon">
                    {phase.horizon}
                  </p>

                  <h3>{phase.objective}</h3>
                </div>

                <span className="governance-roadmap-phase-count">
                  {phase.itemCount}{" "}
                  {phase.itemCount === 1
                    ? "intervention"
                    : "interventions"}
                </span>
              </header>

              {orderedItems.length === 0 ? (
                <div className="governance-roadmap-empty">
                  <strong>
                    No governed interventions assigned
                  </strong>

                  <p>
                    The assessment engine did not assign an
                    intervention to this horizon.
                  </p>
                </div>
              ) : (
                <div className="governance-roadmap-items">
                  {orderedItems.map((item) => (
                    <article
                      className="governance-roadmap-item"
                      key={item.roadmapItemId}
                    >
                      <div className="governance-roadmap-item-heading">
                        <div className="governance-roadmap-sequence">
                          <span>Sequence</span>
                          <strong>{item.sequence}</strong>
                        </div>

                        <div className="governance-roadmap-title">
                          <div className="governance-roadmap-badges">
                            <span className="governance-roadmap-status">
                              {humanize(item.status)}
                            </span>

                            <span className="governance-roadmap-type">
                              {humanize(
                                item.interventionType
                              )}
                            </span>
                          </div>

                          <h4>{item.title}</h4>

                          <p>
                            Owner:{" "}
                            <strong>{item.ownerRole}</strong>
                          </p>
                        </div>

                        <div className="governance-roadmap-value">
                          <span>Value score</span>
                          <strong>
                            {score(item.valueScore)}
                          </strong>
                        </div>
                      </div>

                      <div className="governance-roadmap-outcome">
                        <span>Measurable outcome</span>
                        <p>{item.measurableOutcome}</p>
                      </div>

                      <div className="governance-roadmap-item-meta">
                        <div>
                          <span>
                            Implementation burden
                          </span>
                          <strong>
                            {percent(
                              item.implementationBurden
                            )}
                          </strong>
                        </div>

                        <div>
                          <span>Dependencies</span>
                          <strong>
                            {item.dependencyIds.length}
                          </strong>
                        </div>
                      </div>

                      {item.dependencyIds.length > 0 && (
                        <div className="governance-roadmap-dependencies">
                          <span>
                            Governed dependency references
                          </span>

                          <ul>
                            {item.dependencyIds.map(
                              (dependencyId) => (
                                <li key={dependencyId}>
                                  <code>
                                    {dependencyId}
                                  </code>
                                </li>
                              )
                            )}
                          </ul>
                        </div>
                      )}
                    </article>
                  ))}
                </div>
              )}
            </section>
          );
        })}
      </div>

      <footer className="governance-roadmap-footer">
        <div>
          <strong>Authority boundary</strong>
          <p>
            The interface does not infer execution timing,
            sequencing, ownership, dependencies, or status.
            It displays the governed roadmap artifact
            produced by the backend.
          </p>
        </div>

        <div className="governance-roadmap-provenance">
          {schemaVersion && (
            <span>
              Schema <code>{schemaVersion}</code>
            </span>
          )}

          {roadmapHash && (
            <span>
              Roadmap{" "}
              <code>{roadmapHash.slice(0, 12)}…</code>
            </span>
          )}

          {interventionPlanHash && (
            <span>
              Plan{" "}
              <code>
                {interventionPlanHash.slice(0, 12)}…
              </code>
            </span>
          )}
        </div>
      </footer>
    </section>
  );
}