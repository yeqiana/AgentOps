import { UI_TEXT } from "../../../constants/uiText";
import type { TraceGraphEdge, TraceGraphNode } from "../types/traceConsole";

interface TraceGraphPanelProps {
  nodes: TraceGraphNode[];
  edges: TraceGraphEdge[];
}

export function TraceGraphPanel({ nodes, edges }: TraceGraphPanelProps) {
  return (
    <section className="panel detail-panel">
      <div className="detail-panel-header">
        <div>
          <p className="detail-panel-kicker">{UI_TEXT.panel.graph}</p>
          <h3>{UI_TEXT.panel.simpleStructure}</h3>
        </div>
        <span className="detail-count">{UI_TEXT.pagination.structureCount(nodes.length, edges.length)}</span>
      </div>

      <div className="graph-simple-grid">
        <div>
          <h4>{UI_TEXT.panel.nodes}</h4>
          {nodes.length === 0 ? (
            <p className="muted-text">{UI_TEXT.state.noStructureNodes}</p>
          ) : (
            <ul className="graph-list">
              {nodes.map((node) => (
                <li key={node.node_id}>
                  <strong>{node.title}</strong>
                  <span>
                    {node.node_type} · {node.subtitle || "-"} · {node.happened_at || "-"}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div>
          <h4>{UI_TEXT.panel.edges}</h4>
          {edges.length === 0 ? (
            <p className="muted-text">{UI_TEXT.state.noStructureEdges}</p>
          ) : (
            <ul className="graph-list">
              {edges.map((edge, index) => (
                <li key={`${edge.source_id}-${edge.target_id}-${index}`}>
                  <strong>{edge.edge_type}</strong>
                  <span>
                    {edge.source_id} {"->"} {edge.target_id}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </section>
  );
}
