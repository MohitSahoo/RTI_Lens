import React, { useEffect, useState, useCallback } from 'react';
import { 
  ReactFlow, 
  Background, 
  Controls, 
  MiniMap,
  useNodesState,
  useEdgesState,
  addEdge,
  useReactFlow,
  ReactFlowProvider
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import dagre from 'dagre';
import { GlassCard } from '../ui/GlassCard';

const dagreGraph = new dagre.graphlib.Graph();
dagreGraph.setDefaultEdgeLabel(() => ({}));

const nodeWidth = 200;
const nodeHeight = 60;

const getLayoutedElements = (nodes: any[], edges: any[], direction = 'TB') => {
  const isHorizontal = direction === 'LR';
  dagreGraph.setGraph({ rankdir: direction });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: nodeWidth, height: nodeHeight });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  nodes.forEach((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    node.targetPosition = isHorizontal ? 'left' : 'top';
    node.sourcePosition = isHorizontal ? 'right' : 'bottom';

    node.position = {
      x: nodeWithPosition.x - nodeWidth / 2,
      y: nodeWithPosition.y - nodeHeight / 2,
    };

    return node;
  });

  return { nodes, edges };
};

const GraphInner: React.FC = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [loading, setLoading] = useState(true);
  const { fitView } = useReactFlow();

  const fetchGraphData = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/graph');
      if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);
      const data = await response.json();

      if (!data.nodes || data.nodes.length === 0) {
        setLoading(false);
        return;
      }

      const initialNodes = data.nodes.map((n: any) => ({
        id: String(n.id),
        data: { label: n.name },
        position: { x: 0, y: 0 },
        style: { 
          background: n.type === 'ministry' ? 'rgba(0, 212, 255, 0.1)' : 
                     n.type === 'section' ? 'rgba(124, 58, 237, 0.1)' : 
                     'rgba(0, 255, 157, 0.1)',
          color: '#fff',
          border: `2px solid ${n.type === 'ministry' ? '#00D4FF' : 
                               n.type === 'section' ? '#7C3AED' : 
                               '#00FF9D'}`,
          borderRadius: '12px',
          fontSize: '11px',
          fontWeight: '700',
          width: nodeWidth,
          padding: '10px',
          textAlign: 'center',
          boxShadow: `0 0 20px ${n.type === 'ministry' ? 'rgba(0, 212, 255, 0.2)' : 
                                n.type === 'section' ? 'rgba(124, 58, 237, 0.2)' : 
                                'rgba(0, 255, 157, 0.2)'}`,
        },
      }));

      const initialEdges = data.edges.map((e: any, i: number) => ({
        id: `e-${i}`,
        source: String(e.source),
        target: String(e.target),
        label: e.type,
        animated: true,
        style: { 
          stroke: e.type === 'cites' ? '#7C3AED' : '#00FF9D',
          strokeWidth: 2,
        },
        labelStyle: { fill: '#fff', fontSize: 9, fontWeight: 'bold' },
      }));

      const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
        initialNodes,
        initialEdges
      );

      setNodes(layoutedNodes);
      setEdges(layoutedEdges);
      
      // Force fitView with animation after layout
      setTimeout(() => {
        fitView({ padding: 0.3, duration: 1000 });
      }, 300);
      
    } catch (err: any) {
      console.error('Error loading graph:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGraphData();
  }, []);

  const onConnect = useCallback(
    (params: any) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold font-display">Legal Knowledge Graph</h1>
          <p className="text-white/50 text-sm">Interactive visualization of RTI citations and legal outcome flows.</p>
        </div>
        <div className="flex gap-2">
          <button 
            onClick={() => fetchGraphData()}
            className="px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-xs font-bold uppercase tracking-widest hover:bg-white/10 transition-colors"
          >
            Reset View & Fit
          </button>
        </div>
      </div>

      <GlassCard className="relative bg-black/20 overflow-hidden" style={{ height: '700px', width: '100%' }}>
        {loading && (
          <div className="absolute inset-0 bg-background/50 backdrop-blur-sm z-50 flex items-center justify-center">
            <div className="flex flex-col items-center gap-3">
              <div className="w-10 h-10 border-2 border-primary border-t-transparent rounded-full animate-spin" />
              <span className="text-xs font-bold text-primary animate-pulse uppercase tracking-widest">Constructing Graph...</span>
            </div>
          </div>
        )}
        
        <div className="absolute top-4 left-4 z-10 space-y-2">
          <div className="p-4 rounded-xl bg-background/80 backdrop-blur-md border border-white/10 text-[10px] font-bold uppercase tracking-widest shadow-2xl">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-3 h-3 rounded-full bg-[#00D4FF]" />
              <span>Ministries</span>
            </div>
            <div className="flex items-center gap-3 mb-3">
              <div className="w-3 h-3 rounded-full bg-[#7C3AED]" />
              <span>Sections</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 rounded-full bg-[#00FF9D]" />
              <span>Outcomes</span>
            </div>
          </div>
        </div>
        
        <div style={{ width: '100%', height: '700px' }}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            fitView
            colorMode="dark"
          >
            <Background color="#1e293b" gap={20} size={1} />
            <Controls />
            <MiniMap 
              style={{ background: 'rgba(15, 23, 42, 0.8)' }}
              maskColor="rgba(11, 16, 32, 0.6)"
            />
          </ReactFlow>
        </div>
      </GlassCard>
    </div>
  );
};

const KnowledgeGraph: React.FC = () => (
  <ReactFlowProvider>
    <GraphInner />
  </ReactFlowProvider>
);

export default KnowledgeGraph;
