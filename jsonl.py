import json
from .unfolder import Exporter


class Jsonl(Exporter):
    """JSON exporter for unfolded mesh edges"""

    def __init__(self, properties):
        self.page_size = M.Vector((properties.output_size_x, properties.output_size_y))
        self.style = properties.style
        margin = properties.output_margin
        self.margin = M.Vector((margin, margin))
        self.pure_net = (properties.output_type == 'NONE')
        self.do_create_stickers = properties.do_create_stickers
        self.text_size = properties.sticker_width
        self.angle_epsilon = properties.angle_epsilon

    def format_vertex(self, vector):
        """Convert a vector into scaled 2D coordinates (same scaling as svg.py)."""
        return [
            (vector.x + self.margin.x) * 1000,
            (self.page_size.y - vector.y - self.margin.y) * 1000
        ]

    def write(self, mesh, filename):
        """Write unfolded data to JSON."""
        all_pages = []

        for page in mesh.pages:
            page_data = {
                "name": page.name,
                "width": self.page_size.x * 1000,
                "height": self.page_size.y * 1000,
                "islands": []
            }

            for island in page.islands:
                island_data = {
                    "name": island.title or "",
                    "edges": []
                }

                # iterate over all edges in the island
                for loop, uvedge in island.edges.items():
                    edge = mesh.edges[loop.edge]

                    # vertices of AB in UV
                    A = self.format_vertex(uvedge.va.co + island.pos)
                    B = self.format_vertex(uvedge.vb.co + island.pos)

                    # third vertex of triangle ABC
                    face = uvedge.uvface
                    C = None
                    for uv_vert in face.vertices.values():  # depends on how UVFace stores verts
                        if uv_vert not in (uvedge.va, uvedge.vb):
                            C = self.format_vertex(uv_vert.co + island.pos)
                            break

                    # determine edge category
                    if edge.force_cut:
                        edge_category = "seam_edge"
                    elif uvedge in island.boundary:
                        edge_category = "boundary_edge"
                    else:
                        edge_category = "connection_edge"

                    link_faces = uvedge.loop.edge.link_faces
                    normal1 = list(face.face.normal)
                    if edge_category == "connection_edge":  # two faces share the edge
                        other_face = link_faces[1] if link_faces[0] == face else link_faces[0]
                        normal2 = list(other_face.normal)
                    else:  # boundary edge
                        normal2 = None

                    edge_data = [
                        A[0], A[1], B[0], B[1],
                        C[0] if C else None, C[1] if C else None,
                        edge_category,
                        face.face.index,
                        loop.edge.index,
                        normal1,
                        normal2
                    ]
                    island_data["edges"].append(edge_data)

                page_data["islands"].append(island_data)

            all_pages.append(page_data)

        # write JSON to file
        with open(filename, "w") as f:
            json.dump(all_pages, f, indent=2)
