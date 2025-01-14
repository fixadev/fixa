"use client";

import React, { useCallback, useEffect, useMemo, useState } from "react";
import Dagre from "@dagrejs/dagre";
import {
  ReactFlow,
  useNodesState,
  useEdgesState,
  addEdge,
  type Connection,
  type NodeProps,
  Handle,
  Position,
  type Node,
  type Edge,
  useReactFlow,
  type EdgeProps,
  BaseEdge,
  getSimpleBezierPath,
  MarkerType,
} from "@xyflow/react";

import "@xyflow/react/dist/style.css";

enum HoverState {
  HOVER = "hover",
  DEFAULT = "default",
  DISABLED = "disabled",
}

type StateNode = Node<{
  label: string;
  numFailures?: number;
  numForwards?: number;
  numSuccesses?: number;
  hoverState: HoverState;
}>;

type ResultNode = Node<{
  label: string;
  type: "failure" | "forward" | "success";
  numCalls?: number;
  hoverState: HoverState;
}>;

type StateEdge = Edge<{
  hoverState: HoverState;
  percentage?: number;
}>;

const totalCalls = 1355;
const initialNodes = [
  {
    id: "1",
    type: "state",
    position: { x: 0, y: 0 },
    data: {
      label: "Start of conversation",
      numSuccesses: totalCalls,
      hoverState: HoverState.DEFAULT,
    },
  },
  {
    id: "2",
    type: "state",
    position: { x: 0, y: 0 },
    data: {
      label: "General question",
      numFailures: 100,
      numSuccesses: 200,
      hoverState: HoverState.DEFAULT,
    },
  },
  {
    id: "3",
    type: "state",
    position: { x: 0, y: 0 },
    data: {
      label: "Order takeout",
      numFailures: 10,
      numSuccesses: 100,
      hoverState: HoverState.DEFAULT,
    },
  },
  {
    id: "4",
    type: "state",
    position: { x: 0, y: 0 },
    data: {
      label: "Make reservation",
      numFailures: 100,
      numForwards: 10,
      numSuccesses: 500,
      hoverState: HoverState.DEFAULT,
    },
  },
  {
    id: "4a",
    type: "state",
    position: { x: 0, y: 0 },
    data: {
      label: "Group < 6 people",
      numFailures: 15,
      numForwards: 30,
      numSuccesses: 105,
      hoverState: HoverState.DEFAULT,
    },
  },
  {
    id: "4b",
    type: "state",
    position: { x: 0, y: 0 },
    data: {
      label: "Group ≥ 6 people",
      numFailures: 250,
      numForwards: 60,
      numSuccesses: 40,
      hoverState: HoverState.DEFAULT,
    },
  },
  {
    id: "5",
    type: "result",
    position: { x: 0, y: 0 },
    data: {
      label: "Failure",
      numCalls: 475,
      type: "failure",
      hoverState: HoverState.DEFAULT,
    },
  },
  {
    id: "6",
    type: "result",
    position: { x: 0, y: 0 },
    data: {
      label: "Forward call to human",
      numCalls: 100,
      type: "forward",
      hoverState: HoverState.DEFAULT,
    },
  },
  {
    id: "7",
    type: "result",
    position: { x: 0, y: 0 },
    data: {
      label: "Success",
      numCalls: 445,
      type: "success",
      hoverState: HoverState.DEFAULT,
    },
  },
] as (StateNode | ResultNode)[];
const edgeRelations = [
  {
    source: "1",
    targets: ["2", "3", "4"],
  },
  {
    source: "2",
    targets: ["5", "6", "7"],
  },
  {
    source: "3",
    targets: ["5", "6", "7"],
  },
  {
    source: "4",
    targets: ["5", "6", "4a", "4b"],
  },
  {
    source: "4a",
    targets: ["5", "6", "7"],
  },
  {
    source: "4b",
    targets: ["5", "6", "7"],
  },
];

function getTotalCallsForNode(node: StateNode | ResultNode): number {
  if (node.type === "result") {
    return (node as ResultNode).data.numCalls ?? 0;
  }
  return (
    ((node as StateNode).data.numFailures ?? 0) +
    ((node as StateNode).data.numForwards ?? 0) +
    ((node as StateNode).data.numSuccesses ?? 0)
  );
}

const initialEdges: StateEdge[] = edgeRelations.flatMap(
  ({ source, targets }) => {
    const sourceNode = initialNodes.find((n) => n.id === source);
    if (!sourceNode) return [];

    return targets
      .map((target) => {
        const targetNode = initialNodes.find((n) => n.id === target)!;

        let sourceCalls = 0;
        if (targetNode.type === "result") {
          // For result nodes, only count the specific type of calls
          switch ((targetNode as ResultNode).data.type) {
            case "success":
              sourceCalls = (sourceNode as StateNode).data.numSuccesses ?? 0;
              break;
            case "failure":
              sourceCalls = (sourceNode as StateNode).data.numFailures ?? 0;
              break;
            case "forward":
              sourceCalls = (sourceNode as StateNode).data.numForwards ?? 0;
              break;
            default:
              sourceCalls = 0;
          }
        } else {
          sourceCalls = getTotalCallsForNode(sourceNode);
        }

        if (sourceCalls === 0) return null;

        const targetTotalCalls = getTotalCallsForNode(targetNode);

        const percentage =
          targetNode.type === "result"
            ? sourceCalls / targetTotalCalls
            : targetTotalCalls / sourceCalls;

        return {
          id: `e${source}-${target}`,
          type: "stateEdge",
          source,
          target,
          data: {
            percentage,
            hoverState: HoverState.DEFAULT,
          },
          markerEnd: { type: MarkerType.Arrow },
        };
      })
      .filter((e) => e !== null);
  },
);
console.log(initialEdges);

export default function FlowChart({
  selectedNodeId,
  onSelectNodeId,
}: {
  selectedNodeId: string | null;
  onSelectNodeId: (nodeId: string | null) => void;
}) {
  const nodeTypes = useMemo(
    () => ({ state: StateNode, result: ResultNode }),
    [],
  );
  const edgeTypes = useMemo(() => ({ stateEdge: StateEdge }), []);
  const { fitView, fitBounds, viewportInitialized } = useReactFlow();
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [, setHoveredNodeId] = useState<string | null>(null);
  // const [hoveredEdgeId, setHoveredEdgeId] = useState<string | null>(null);
  const adjacencyMap = useMemo(() => buildAdjacencyMap(edges), [edges]);
  const [nodesMeasured, setNodesMeasured] = useState(false);

  useEffect(() => {
    if (!selectedNodeId) {
      // Node was deselected
      setNodes((nds) =>
        nds.map((n) => ({
          ...n,
          data: { ...n.data, hoverState: HoverState.DEFAULT },
        })),
      );
      return;
    }

    // Find the node that matches the call's node ID
    const nodeToZoom = nodes.find((n) => n.id === selectedNodeId);
    if (nodeToZoom) {
      onSelectNodeId(nodeToZoom.id);
      setNodes((nds) =>
        nds.map((n) => ({
          ...n,
          data: {
            ...n.data,
            hoverState:
              n.id === nodeToZoom.id ? HoverState.HOVER : HoverState.DISABLED,
          },
        })),
      );
      // Zoom to the node with some padding
      void (async () => {
        const width = nodeToZoom.measured?.width ?? 0;
        const height = nodeToZoom.measured?.height ?? 0;
        await fitBounds(
          {
            x: nodeToZoom.position.x,
            y: nodeToZoom.position.y + height,
            width: width,
            height: height + height * 2,
          },
          { padding: 2, duration: 600 },
        );
      })();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedNodeId]);

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges],
  );

  useEffect(() => {
    if (!viewportInitialized) return;
    if (!nodesMeasured) {
      setNodes((nodes) =>
        nodes.map((node) => {
          const element = document.getElementById(`node-${node.id}`);
          const measured = element?.getBoundingClientRect();

          return {
            ...node,
            measured: {
              width: measured?.width ?? 0,
              height: measured?.height ?? 0,
            },
          };
        }),
      );
      setNodesMeasured(true);
    }
  }, [nodesMeasured, setNodes, viewportInitialized]);

  useEffect(() => {
    if (!nodesMeasured) return;

    const layouted = getLayoutedElements(nodes, edges, { direction: "TB" });
    setNodes([...layouted.nodes] as StateNode[]);
    setEdges([...layouted.edges] as StateEdge[]);

    window.requestAnimationFrame(() => {
      void fitView();
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodesMeasured]);

  const onNodeMouseEnter = useCallback(
    (_: React.MouseEvent, node: Node) => {
      setHoveredNodeId(node.id);

      // Get adjacent node IDs from adjacency map
      const adjacentNodes = adjacencyMap.get(node.id) ?? new Set();

      setNodes((nds) =>
        nds.map((n) => ({
          ...n,
          data: {
            ...n.data,
            hoverState:
              n.id === node.id || adjacentNodes.has(n.id)
                ? HoverState.HOVER
                : HoverState.DISABLED,
          },
        })),
      );

      // Calculate total incoming and outgoing flow for hovered node
      // const nodeData = node.data as StateNode["data"];
      const totalNodeFlow = getTotalCallsForNode(
        node as StateNode | ResultNode,
      );

      setEdges((eds) =>
        eds.map((e) => {
          const isConnected = e.source === node.id || e.target === node.id;
          let newPercentage = e.data?.percentage;

          if (isConnected) {
            if (e.source === node.id) {
              // Outgoing edge - percentage relative to total outgoing flow
              const targetNode = initialNodes.find((n) => n.id === e.target)!;
              const curFlow = getTotalCallsForNode(targetNode);
              if (targetNode.type === "result") {
                switch ((targetNode as ResultNode).data.type) {
                  case "success":
                    newPercentage =
                      ((node as StateNode).data.numSuccesses ?? 0) /
                      totalNodeFlow;
                    break;
                  case "forward":
                    newPercentage =
                      ((node as StateNode).data.numForwards ?? 0) /
                      totalNodeFlow;
                    break;
                  case "failure":
                    newPercentage =
                      ((node as StateNode).data.numFailures ?? 0) /
                      totalNodeFlow;
                    break;
                }
              } else {
                newPercentage = curFlow / totalNodeFlow;
              }
            } else {
              // Incoming edge - keep original percentage (relative to parent's flow)
              newPercentage = e.data?.percentage;
            }
          }

          return {
            ...e,
            data: {
              ...e.data,
              hoverState: isConnected ? HoverState.HOVER : HoverState.DISABLED,
              percentage: newPercentage,
            },
          };
        }),
      );
    },
    [setNodes, setEdges, adjacencyMap],
  );

  // Don't forget to reset percentages when mouse leaves
  const onNodeMouseLeave = useCallback(() => {
    setHoveredNodeId(null);
    if (selectedNodeId) {
      setNodes((nds) =>
        nds.map((n) => ({
          ...n,
          data: {
            ...n.data,
            hoverState:
              n.id === selectedNodeId ? HoverState.HOVER : HoverState.DISABLED,
          },
        })),
      );
    } else {
      setNodes((nds) =>
        nds.map((n) => ({
          ...n,
          data: { ...n.data, hoverState: HoverState.DEFAULT },
        })),
      );
    }
    setEdges((eds) =>
      eds.map((e) => ({
        ...e,
        data: {
          ...e.data,
          hoverState: HoverState.DEFAULT,
          percentage: initialEdges.find((ie) => ie.id === e.id)?.data
            ?.percentage,
        },
      })),
    );
  }, [setNodes, setEdges, selectedNodeId]);

  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      // If clicking the already selected node, deselect it
      if (node.id === selectedNodeId) {
        onSelectNodeId(null);
      } else {
        onSelectNodeId(node.id);
      }
    },
    [selectedNodeId, onSelectNodeId],
  );

  // const onEdgeMouseEnter = useCallback(
  //   (_: React.MouseEvent, edge: Edge) => {
  //     setHoveredEdgeId(edge.id);

  //     // Highlight the edge
  //     setEdges((eds) =>
  //       eds.map((e) => ({
  //         ...e,
  //         data: {
  //           ...e.data,
  //           hoverState:
  //             e.id === edge.id ? HoverState.HOVER : HoverState.DISABLED,
  //         },
  //       })),
  //     );

  //     // Highlight the connected nodes
  //     setNodes((nds) =>
  //       nds.map((n) => ({
  //         ...n,
  //         data: {
  //           ...n.data,
  //           hoverState:
  //             n.id === edge.source || n.id === edge.target
  //               ? HoverState.HOVER
  //               : HoverState.DISABLED,
  //         },
  //       })),
  //     );
  //   },
  //   [setEdges, setNodes],
  // );

  // const onEdgeMouseLeave = useCallback(() => {
  //   setHoveredEdgeId(null);

  //   // Reset edge highlighting
  //   setEdges((eds) =>
  //     eds.map((e) => ({
  //       ...e,
  //       data: { ...e.data, hoverState: HoverState.DEFAULT },
  //     })),
  //   );

  //   // Reset node highlighting
  //   setNodes((nds) =>
  //     nds.map((n) => ({
  //       ...n,
  //       data: { ...n.data, hoverState: HoverState.DEFAULT },
  //     })),
  //   );
  // }, [setEdges, setNodes]);

  return (
    <div style={{ width: "100vw", height: "100vh" }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        fitView
        onNodeMouseEnter={onNodeMouseEnter}
        onNodeMouseLeave={onNodeMouseLeave}
        onNodeClick={onNodeClick}
        // onEdgeMouseEnter={onEdgeMouseEnter}
        // onEdgeMouseLeave={onEdgeMouseLeave}
      />
    </div>
  );
}

function getLayoutedElements(
  nodes: Node[],
  edges: Edge[],
  options: Record<string, string>,
) {
  const g = new Dagre.graphlib.Graph().setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: options.direction, ranksep: 200 });

  edges.forEach((edge) => g.setEdge(edge.source, edge.target));
  nodes.forEach((node) =>
    g.setNode(node.id, {
      ...node,
      width: node.measured?.width ?? 0,
      height: node.measured?.height ?? 0,
    }),
  );

  Dagre.layout(g);

  return {
    nodes: nodes.map((node) => {
      const position = g.node(node.id);
      // We are shifting the dagre node position (anchor=center center) to the top left
      // so it matches the React Flow node anchor point (top left).
      const x = position.x - (node.measured?.width ?? 0) / 2;
      const y = position.y - (node.measured?.height ?? 0) / 2;

      return { ...node, position: { x, y } };
    }),
    edges,
  };
}

function buildAdjacencyMap(edges: StateEdge[]): Map<string, Set<string>> {
  const adjacencyMap = new Map<string, Set<string>>();

  edges.forEach((edge) => {
    // Initialize sets if they don't exist
    if (!adjacencyMap.has(edge.source)) {
      adjacencyMap.set(edge.source, new Set());
    }
    if (!adjacencyMap.has(edge.target)) {
      adjacencyMap.set(edge.target, new Set());
    }

    // Add bidirectional connections
    adjacencyMap.get(edge.source)!.add(edge.target);
    adjacencyMap.get(edge.target)!.add(edge.source);
  });

  return adjacencyMap;
}

const RED = "#FE331B";
const YELLOW = "#FDCD2E";
const GREEN = "#90CF27";

function StateNode({ id, data }: NodeProps<StateNode>) {
  const percentageOfTotalCalls = useMemo(() => {
    return (
      ((data.numFailures ?? 0) +
        (data.numForwards ?? 0) +
        (data.numSuccesses ?? 0)) /
      totalCalls
    );
  }, [data.numFailures, data.numForwards, data.numSuccesses]);

  const padding = useMemo(() => {
    return {
      horizontal: 2 + percentageOfTotalCalls * 8,
      vertical: 0.5 + percentageOfTotalCalls * 4,
    };
  }, [percentageOfTotalCalls]);

  const gradient = useMemo(() => {
    const total =
      (data.numFailures ?? 0) +
      (data.numForwards ?? 0) +
      (data.numSuccesses ?? 0);
    if (total === 0) return "white";

    const failurePercent = ((data.numFailures ?? 0) / total) * 100;
    const forwardPercent = ((data.numForwards ?? 0) / total) * 100;

    return `linear-gradient(to right, 
      ${RED} 0%, 
      ${RED} ${failurePercent}%, 
      ${YELLOW} ${failurePercent}%, 
      ${YELLOW} ${failurePercent + forwardPercent}%, 
      ${GREEN} ${failurePercent + forwardPercent}%, 
      ${GREEN} 100%
    )`;
  }, [data.numFailures, data.numForwards, data.numSuccesses]);

  const fontSize = useMemo(() => {
    // Scale from 0.75rem to 1.5rem based on percentage of total calls
    return 0.5 + percentageOfTotalCalls * 0.5;
  }, [percentageOfTotalCalls]);

  const textPadding = useMemo(() => {
    return 0.25 + percentageOfTotalCalls * 0.5;
  }, [percentageOfTotalCalls]);

  const getOpacityForState = (state: HoverState) => {
    switch (state) {
      case HoverState.HOVER:
        return 1;
      case HoverState.DISABLED:
        return 0.2;
      default:
        return 1;
    }
  };

  return (
    <>
      <Handle className="z-10" type="target" position={Position.Top} />
      <div
        id={`node-${id}`}
        className="relative rounded-md p-6 shadow-sm outline outline-2 outline-input"
        style={{
          padding: `${padding.vertical}rem ${padding.horizontal}rem`,
          // width: `${2 * padding.horizontal}rem`,
          // height: `${2 * padding.vertical}rem`,
          background: gradient,
          transform:
            data.hoverState === HoverState.HOVER ? "scale(1.05)" : "scale(1)",
          transition: "transform 0.1s ease-in-out",
          opacity: getOpacityForState(data.hoverState),
        }}
      >
        <span className="invisible" style={{ fontSize: `${fontSize}rem` }}>
          {data.label}
        </span>
        <div
          className="absolute rounded-md bg-white shadow-sm"
          style={{
            fontSize: `${fontSize}rem`,
            padding: `${textPadding}rem`,
            top: `${textPadding}rem`,
            left: `${textPadding}rem`,
          }}
        >
          {data.label}
        </div>
        <div className="absolute bottom-0 left-0 h-[20%] w-full rounded-b-md bg-black/10"></div>
      </div>
      <Handle type="source" position={Position.Bottom} />
    </>
  );
}

function ResultNode({ id, data }: NodeProps<ResultNode>) {
  const percentageOfTotalCalls = useMemo(
    () => (data.numCalls ?? 0) / totalCalls,
    [data.numCalls],
  );

  const padding = useMemo(() => {
    return {
      horizontal: 2 + percentageOfTotalCalls * 8,
      vertical: 1 + percentageOfTotalCalls * 4,
    };
  }, [percentageOfTotalCalls]);

  const backgroundColor = useMemo(() => {
    switch (data.type) {
      case "success":
        return GREEN;
      case "failure":
        return RED;
      case "forward":
        return YELLOW;
      default:
        return "white";
    }
  }, [data.type]);

  const getOpacityForState = (state: HoverState) => {
    switch (state) {
      case HoverState.HOVER:
        return 1;
      case HoverState.DISABLED:
        return 0.2;
      default:
        return 1;
    }
  };

  return (
    <>
      <Handle className="z-10" type="target" position={Position.Top} />
      <div
        id={`node-${id}`}
        className="relative rounded-md shadow-sm outline outline-2"
        style={{
          padding: `${padding.vertical}rem ${padding.horizontal}rem`,
          // width: `${2 * padding.horizontal}rem`,
          // height: `${2 * padding.vertical}rem`,
          // backgroundColor: `${backgroundColor}1A`,
          backgroundColor: "white",
          outlineColor: backgroundColor,
          transform:
            data.hoverState === HoverState.HOVER ? "scale(1.05)" : "scale(1)",
          transition: "transform 0.1s ease-in-out",
          opacity: getOpacityForState(data.hoverState),
        }}
      >
        {data.label}
        <div
          className="absolute left-0 top-0 h-[20%] w-full rounded-t-md"
          style={{ backgroundColor }}
        ></div>
      </div>
    </>
  );
}

function StateEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  markerEnd,
  data,
}: EdgeProps<StateEdge>) {
  const [edgePath, labelX, labelY] = getSimpleBezierPath({
    sourceX,
    sourceY,
    targetX,
    targetY,
  });

  const getOpacityForState = (state: HoverState) => {
    switch (state) {
      case HoverState.HOVER:
        return 1;
      case HoverState.DISABLED:
        return 0.1;
      default:
        return 0.5;
    }
  };

  return (
    <>
      <BaseEdge
        id={id}
        path={edgePath}
        markerEnd={markerEnd}
        style={{
          strokeWidth: data?.hoverState === HoverState.HOVER ? 2 : 1,
          opacity: getOpacityForState(data?.hoverState ?? HoverState.DEFAULT),
          strokeDasharray:
            data?.hoverState === HoverState.HOVER ? "6 6" : "none",
          animation:
            data?.hoverState === HoverState.HOVER
              ? "flowingDash 0.5s linear infinite"
              : "none",
        }}
      />
      {data?.hoverState === HoverState.HOVER &&
        data?.percentage !== undefined && (
          <>
            <circle
              cx={labelX}
              cy={labelY}
              r={Math.max(15, 15 + data.percentage * 30)}
              fill="white"
              stroke="#D3D3D3"
              strokeWidth="1"
              className="pointer-events-none"
            />
            <text
              x={labelX}
              y={labelY}
              textAnchor="middle"
              dominantBaseline="middle"
              className="pointer-events-none text-xs font-medium"
              style={{
                fontSize: `${Math.max(10, 10 + data.percentage * 10)}px`,
                fill: `rgba(0, 0, 0, ${0.5 + data.percentage * 0.7})`,
              }}
            >
              {`${Math.round(data.percentage * 100)}%`}
            </text>
          </>
        )}
    </>
  );
}
