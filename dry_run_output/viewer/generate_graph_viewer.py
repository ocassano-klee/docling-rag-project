"""
Générateur de visualisation interactive du graphe Neptune
Lit tous les CSV neptune_inserts_*.csv et génère une page HTML interactive
"""

import csv
import json
import os
from pathlib import Path
from collections import defaultdict
import re


class NeptuneGraphViewer:
    """Génère une visualisation HTML interactive du graphe Neptune"""
    
    def __init__(self, csv_directory: str = ".."):
        """
        Initialise le générateur
        
        Args:
            csv_directory: Dossier contenant les CSV neptune_inserts_*.csv
        """
        self.csv_directory = Path(csv_directory)
        self.nodes = {}
        self.edges = []
        self.documents = []
        self.topics = []
        self.chunks = []
        self.annotations = []
        
    def parse_csv_files(self):
        """Parse tous les fichiers CSV Neptune"""
        csv_files = list(self.csv_directory.glob("neptune_inserts_*.csv"))
        
        if not csv_files:
            print(f"❌ Aucun fichier neptune_inserts_*.csv trouvé dans {self.csv_directory}")
            return False
        
        print(f"📂 Fichiers CSV trouvés : {len(csv_files)}")
        for csv_file in csv_files:
            print(f"   - {csv_file.name}")
        
        for csv_file in csv_files:
            self._parse_csv_file(csv_file)
        
        print(f"\n📊 Statistiques du graphe :")
        print(f"   - Documents : {len(self.documents)}")
        print(f"   - Chunks : {len(self.chunks)}")
        print(f"   - Topics : {len(self.topics)}")
        print(f"   - Annotations : {len(self.annotations)}")
        print(f"   - Relations : {len(self.edges)}")
        
        return True
    
    def _parse_csv_file(self, csv_file: Path):
        """Parse un fichier CSV Neptune"""
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                query_type = row['query_type']
                query = row['query']
                
                if query_type == 'CREATE_DOCUMENT':
                    self._parse_document(query)
                elif query_type == 'MERGE_TOPIC':
                    self._parse_topic(query)
                elif query_type == 'CREATE_CHUNK':
                    self._parse_chunk(query)
                elif query_type == 'CREATE_ANNOTATION':
                    self._parse_annotation(query)
                elif query_type == 'CREATE_RELATIONSHIP':
                    self._parse_relationship(query)
    
    def _extract_properties(self, query: str) -> dict:
        """Extrait les propriétés d'une requête Cypher"""
        props = {}
        
        # Extraire id
        id_match = re.search(r"id:\s*'([^']+)'", query)
        if id_match:
            props['id'] = id_match.group(1)
        
        # Extraire title
        title_match = re.search(r"title:\s*'([^']+)'", query)
        if title_match:
            props['title'] = title_match.group(1)
        
        # Extraire name
        name_match = re.search(r"name:\s*'([^']+)'", query)
        if name_match:
            props['name'] = name_match.group(1)
        
        # Extraire type
        type_match = re.search(r"type:\s*'([^']+)'", query)
        if type_match:
            props['type'] = type_match.group(1)
        
        # Extraire value
        value_match = re.search(r"value:\s*'([^']+)'", query)
        if value_match:
            props['value'] = value_match.group(1)
        
        # Extraire page
        page_match = re.search(r"page:\s*(\d+)", query)
        if page_match:
            props['page'] = int(page_match.group(1))
        
        # Extraire document_id
        doc_id_match = re.search(r"document_id:\s*'([^']+)'", query)
        if doc_id_match:
            props['document_id'] = doc_id_match.group(1)
        
        return props
    
    def _parse_document(self, query: str):
        """Parse une requête CREATE_DOCUMENT"""
        props = self._extract_properties(query)
        
        if 'id' in props:
            node = {
                'id': props['id'],
                'label': props.get('title', props['id']),
                'type': 'Document',
                'group': 'document',
                'title': props.get('title', ''),
                'color': '#FF6B6B'
            }
            self.nodes[props['id']] = node
            self.documents.append(node)
    
    def _parse_topic(self, query: str):
        """Parse une requête MERGE_TOPIC"""
        props = self._extract_properties(query)
        
        if 'id' in props:
            node = {
                'id': props['id'],
                'label': props.get('name', props['id']),
                'type': 'Topic',
                'group': 'topic',
                'topic_type': props.get('type', 'keyword'),
                'color': '#FFD93D'
            }
            self.nodes[props['id']] = node
            self.topics.append(node)
    
    def _parse_chunk(self, query: str):
        """Parse une requête CREATE_CHUNK"""
        props = self._extract_properties(query)
        
        if 'id' in props:
            node = {
                'id': props['id'],
                'label': f"{props['id']}\nPage {props.get('page', '?')}",
                'type': 'Chunk',
                'group': 'chunk',
                'page': props.get('page'),
                'document_id': props.get('document_id'),
                'color': '#4ECDC4'
            }
            self.nodes[props['id']] = node
            self.chunks.append(node)
    
    def _parse_annotation(self, query: str):
        """Parse une requête CREATE_ANNOTATION"""
        props = self._extract_properties(query)
        
        if 'id' in props:
            node = {
                'id': props['id'],
                'label': f"{props.get('type', '')}\n{props.get('value', '')}",
                'type': 'Annotation',
                'group': 'annotation',
                'ann_type': props.get('type'),
                'value': props.get('value'),
                'color': '#95E1D3'
            }
            self.nodes[props['id']] = node
            self.annotations.append(node)
    
    def _parse_relationship(self, query: str):
        """Parse une requête CREATE_RELATIONSHIP"""
        # Extraire les IDs des nœuds
        parts = query.split("'")
        
        if len(parts) >= 4:
            source_id = parts[1]
            target_id = parts[3]
            
            # Déterminer le type de relation
            if 'HAS_CHUNK' in query:
                rel_type = 'HAS_CHUNK'
                color = '#FF6B6B'
                width = 3
            elif 'ABOUT' in query:
                rel_type = 'ABOUT'
                color = '#FFD93D'
                width = 2.5
            elif 'HAS_ANNOTATION' in query:
                rel_type = 'HAS_ANNOTATION'
                color = '#4ECDC4'
                width = 2
            else:
                rel_type = 'UNKNOWN'
                color = '#999999'
                width = 1
            
            edge = {
                'from': source_id,
                'to': target_id,
                'label': rel_type,
                'color': color,
                'width': width,
                'arrows': 'to'
            }
            self.edges.append(edge)
    
    def generate_html(self, output_file: str = "graph_viewer.html"):
        """Génère le fichier HTML interactif"""
        
        # Préparer les données pour vis.js
        nodes_list = list(self.nodes.values())
        
        # Statistiques pour l'interface
        stats = {
            'documents': len(self.documents),
            'chunks': len(self.chunks),
            'topics': len(self.topics),
            'annotations': len(self.annotations),
            'edges': len(self.edges)
        }
        
        # Trouver les topics partagés (liés à plusieurs documents)
        topic_connections = defaultdict(set)
        for edge in self.edges:
            if edge['label'] == 'ABOUT':
                chunk_id = edge['from']
                topic_id = edge['to']
                
                # Trouver le document parent du chunk
                chunk = self.nodes.get(chunk_id)
                if chunk and 'document_id' in chunk:
                    topic_connections[topic_id].add(chunk['document_id'])
        
        shared_topics = [
            {
                'id': topic_id,
                'name': self.nodes[topic_id]['label'],
                'documents': list(doc_ids)
            }
            for topic_id, doc_ids in topic_connections.items()
            if len(doc_ids) > 1
        ]
        
        html_content = self._generate_html_template(nodes_list, self.edges, stats, shared_topics)
        
        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"\n✅ Visualisation générée : {output_path.absolute()}")
        print(f"   Ouvrez ce fichier dans votre navigateur pour voir le graphe interactif")
        
        if shared_topics:
            print(f"\n🔗 Topics partagés entre documents : {len(shared_topics)}")
            for topic in shared_topics[:5]:
                print(f"   - {topic['name']} : {len(topic['documents'])} documents")
    
    def _generate_html_template(self, nodes, edges, stats, shared_topics):
        """Génère le template HTML"""
        
        return f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Neptune Graph Viewer - Visualisation Interactive</title>
    <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1800px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}
        
        .header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        
        .stats {{
            display: flex;
            justify-content: space-around;
            padding: 20px;
            background: #f8f9fa;
            border-bottom: 2px solid #e9ecef;
        }}
        
        .stat-card {{
            text-align: center;
            padding: 15px 30px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            transition: transform 0.3s;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
        }}
        
        .stat-number {{
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .stat-label {{
            color: #6c757d;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .stat-card.documents .stat-number {{ color: #FF6B6B; }}
        .stat-card.chunks .stat-number {{ color: #4ECDC4; }}
        .stat-card.topics .stat-number {{ color: #FFD93D; }}
        .stat-card.annotations .stat-number {{ color: #95E1D3; }}
        .stat-card.edges .stat-number {{ color: #6c757d; }}
        
        .controls {{
            padding: 20px;
            background: white;
            border-bottom: 2px solid #e9ecef;
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            align-items: center;
        }}
        
        .control-group {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .control-group label {{
            font-weight: 600;
            color: #495057;
        }}
        
        button {{
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s;
            font-size: 0.9em;
        }}
        
        button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}
        
        .btn-primary {{
            background: #667eea;
            color: white;
        }}
        
        .btn-success {{
            background: #51cf66;
            color: white;
        }}
        
        .btn-warning {{
            background: #ffd93d;
            color: #333;
        }}
        
        .btn-info {{
            background: #4ecdc4;
            color: white;
        }}
        
        select {{
            padding: 8px 15px;
            border: 2px solid #e9ecef;
            border-radius: 5px;
            font-size: 0.9em;
            cursor: pointer;
        }}
        
        #mynetwork {{
            width: 100%;
            height: 700px;
            border-top: 2px solid #e9ecef;
        }}
        
        .legend {{
            padding: 20px;
            background: #f8f9fa;
            border-top: 2px solid #e9ecef;
        }}
        
        .legend h3 {{
            margin-bottom: 15px;
            color: #495057;
        }}
        
        .legend-items {{
            display: flex;
            gap: 30px;
            flex-wrap: wrap;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .legend-color {{
            width: 30px;
            height: 30px;
            border-radius: 50%;
            border: 2px solid #333;
        }}
        
        .shared-topics {{
            padding: 20px;
            background: #fff3cd;
            border-top: 2px solid #ffc107;
        }}
        
        .shared-topics h3 {{
            margin-bottom: 15px;
            color: #856404;
        }}
        
        .shared-topics ul {{
            list-style: none;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 10px;
        }}
        
        .shared-topics li {{
            padding: 10px;
            background: white;
            border-radius: 5px;
            border-left: 4px solid #ffc107;
        }}
        
        .shared-topics strong {{
            color: #856404;
        }}
        
        .info-panel {{
            padding: 20px;
            background: #e7f5ff;
            border-top: 2px solid #339af0;
        }}
        
        .info-panel h3 {{
            margin-bottom: 10px;
            color: #1864ab;
        }}
        
        .info-panel p {{
            color: #495057;
            line-height: 1.6;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌐 Neptune Graph Viewer</h1>
            <p>Visualisation interactive du graphe de connaissances</p>
        </div>
        
        <div class="stats">
            <div class="stat-card documents">
                <div class="stat-number">{stats['documents']}</div>
                <div class="stat-label">Documents</div>
            </div>
            <div class="stat-card chunks">
                <div class="stat-number">{stats['chunks']}</div>
                <div class="stat-label">Chunks</div>
            </div>
            <div class="stat-card topics">
                <div class="stat-number">{stats['topics']}</div>
                <div class="stat-label">Topics</div>
            </div>
            <div class="stat-card annotations">
                <div class="stat-number">{stats['annotations']}</div>
                <div class="stat-label">Annotations</div>
            </div>
            <div class="stat-card edges">
                <div class="stat-number">{stats['edges']}</div>
                <div class="stat-label">Relations</div>
            </div>
        </div>
        
        {self._generate_shared_topics_html(shared_topics)}
        
        <div class="controls">
            <div class="control-group">
                <label>Layout :</label>
                <select id="layoutSelect" onchange="changeLayout()">
                    <option value="hierarchical">Hiérarchique</option>
                    <option value="force">Force-directed</option>
                    <option value="circular">Circulaire</option>
                </select>
            </div>
            
            <button class="btn-primary" onclick="focusOnTopics()">🎯 Focus Topics Partagés</button>
            <button class="btn-success" onclick="showAllNodes()">👁️ Tout Afficher</button>
            <button class="btn-warning" onclick="highlightConnections()">🔗 Mettre en évidence les liens</button>
            <button class="btn-info" onclick="resetView()">🔄 Réinitialiser</button>
        </div>
        
        <div id="mynetwork"></div>
        
        <div class="legend">
            <h3>📊 Légende</h3>
            <div class="legend-items">
                <div class="legend-item">
                    <div class="legend-color" style="background: #FF6B6B;"></div>
                    <span><strong>Documents</strong> - Fichiers PDF sources</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #4ECDC4;"></div>
                    <span><strong>Chunks</strong> - Morceaux de texte</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #FFD93D;"></div>
                    <span><strong>Topics</strong> - Concepts partagés (⭐ clé de la liaison !)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #95E1D3;"></div>
                    <span><strong>Annotations</strong> - Métadonnées contextuelles</span>
                </div>
            </div>
        </div>
        
        <div class="info-panel">
            <h3>💡 Comment utiliser cette visualisation</h3>
            <p>
                <strong>🖱️ Navigation :</strong> Cliquez et glissez pour déplacer le graphe. Utilisez la molette pour zoomer.<br>
                <strong>🎯 Sélection :</strong> Cliquez sur un nœud pour voir ses connexions.<br>
                <strong>🔗 Topics partagés :</strong> Les nœuds jaunes (Topics) sont la clé ! Ils lient automatiquement les documents qui partagent les mêmes concepts.<br>
                <strong>📊 Layouts :</strong> Changez le layout pour différentes perspectives du graphe.
            </p>
        </div>
    </div>
    
    <script>
        // Données du graphe
        const nodesData = {json.dumps(nodes, ensure_ascii=False)};
        const edgesData = {json.dumps(edges, ensure_ascii=False)};
        const sharedTopicsData = {json.dumps(shared_topics, ensure_ascii=False)};
        
        // Créer le réseau
        const container = document.getElementById('mynetwork');
        const data = {{
            nodes: new vis.DataSet(nodesData),
            edges: new vis.DataSet(edgesData)
        }};
        
        let options = {{
            nodes: {{
                shape: 'dot',
                size: 20,
                font: {{
                    size: 14,
                    color: '#333',
                    face: 'Segoe UI'
                }},
                borderWidth: 2,
                shadow: true
            }},
            edges: {{
                arrows: {{
                    to: {{
                        enabled: true,
                        scaleFactor: 0.5
                    }}
                }},
                smooth: {{
                    type: 'cubicBezier',
                    forceDirection: 'vertical',
                    roundness: 0.4
                }},
                font: {{
                    size: 10,
                    align: 'middle'
                }}
            }},
            layout: {{
                hierarchical: {{
                    enabled: true,
                    direction: 'UD',
                    sortMethod: 'directed',
                    levelSeparation: 150,
                    nodeSpacing: 200
                }}
            }},
            physics: {{
                enabled: false
            }},
            interaction: {{
                hover: true,
                tooltipDelay: 200,
                navigationButtons: true,
                keyboard: true
            }}
        }};
        
        const network = new vis.Network(container, data, options);
        
        // Fonctions de contrôle
        function changeLayout() {{
            const layout = document.getElementById('layoutSelect').value;
            
            if (layout === 'hierarchical') {{
                network.setOptions({{
                    layout: {{
                        hierarchical: {{
                            enabled: true,
                            direction: 'UD',
                            sortMethod: 'directed'
                        }}
                    }},
                    physics: {{ enabled: false }}
                }});
            }} else if (layout === 'force') {{
                network.setOptions({{
                    layout: {{
                        hierarchical: {{ enabled: false }}
                    }},
                    physics: {{
                        enabled: true,
                        barnesHut: {{
                            gravitationalConstant: -2000,
                            springLength: 200,
                            springConstant: 0.04
                        }}
                    }}
                }});
            }} else if (layout === 'circular') {{
                network.setOptions({{
                    layout: {{
                        hierarchical: {{ enabled: false }}
                    }},
                    physics: {{ enabled: false }}
                }});
                
                // Positionner en cercle
                const nodes = data.nodes.get();
                const angleStep = (2 * Math.PI) / nodes.length;
                const radius = 400;
                
                nodes.forEach((node, index) => {{
                    const angle = index * angleStep;
                    data.nodes.update({{
                        id: node.id,
                        x: radius * Math.cos(angle),
                        y: radius * Math.sin(angle)
                    }});
                }});
            }}
        }}
        
        function focusOnTopics() {{
            const topicIds = sharedTopicsData.map(t => t.id);
            network.selectNodes(topicIds);
            network.fit({{
                nodes: topicIds,
                animation: true
            }});
        }}
        
        function showAllNodes() {{
            network.fit({{ animation: true }});
        }}
        
        function highlightConnections() {{
            const selectedNodes = network.getSelectedNodes();
            
            if (selectedNodes.length === 0) {{
                alert('Sélectionnez d\\'abord un nœud !');
                return;
            }}
            
            const connectedNodes = network.getConnectedNodes(selectedNodes[0]);
            network.selectNodes([selectedNodes[0], ...connectedNodes]);
        }}
        
        function resetView() {{
            network.unselectAll();
            network.fit({{ animation: true }});
        }}
        
        // Event listeners
        network.on('selectNode', function(params) {{
            const nodeId = params.nodes[0];
            const node = data.nodes.get(nodeId);
            console.log('Nœud sélectionné:', node);
        }});
        
        network.on('doubleClick', function(params) {{
            if (params.nodes.length > 0) {{
                const nodeId = params.nodes[0];
                const connectedNodes = network.getConnectedNodes(nodeId);
                network.fit({{
                    nodes: [nodeId, ...connectedNodes],
                    animation: true
                }});
            }}
        }});
        
        // Initialisation
        console.log('Graphe chargé avec succès !');
        console.log('Documents:', {stats['documents']});
        console.log('Topics partagés:', sharedTopicsData.length);
    </script>
</body>
</html>"""
    
    def _generate_shared_topics_html(self, shared_topics):
        """Génère le HTML pour les topics partagés"""
        if not shared_topics:
            return ""
        
        topics_html = "\n".join([
            f"<li><strong>{topic['name']}</strong> : {len(topic['documents'])} documents liés</li>"
            for topic in shared_topics[:10]
        ])
        
        return f"""
        <div class="shared-topics">
            <h3>🔗 Topics Partagés (Liens entre documents)</h3>
            <ul>
                {topics_html}
            </ul>
        </div>
        """


def main():
    """Point d'entrée principal"""
    print("=" * 60)
    print("🌐 Neptune Graph Viewer Generator")
    print("=" * 60)
    print()
    
    # Créer le générateur
    viewer = NeptuneGraphViewer(csv_directory="..")
    
    # Parser les CSV
    if not viewer.parse_csv_files():
        return
    
    # Générer le HTML
    viewer.generate_html("graph_viewer.html")
    
    print()
    print("=" * 60)
    print("✅ Génération terminée !")
    print("=" * 60)


if __name__ == "__main__":
    main()
