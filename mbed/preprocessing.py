from mbed.trimming import edge_lengths, find_edges
from mbed.generation import make_line_mesh
from math import ceil
import numpy as np


def refine(mesh, threshold):
    '''Refine such that the new mesh has cell size of at most dx'''
    assert mesh.topology().dim() == 1

    e2v = mesh.topology()(1, 0)

    cells = {old: [c.tolist()] for old, c in enumerate(mesh.cells())}
    x = mesh.coordinates()
    
    lengths = edge_lengths(mesh)
    needs_refine = find_edges(lengths, predicate=lambda v, x: v > threshold)

    next_v = len(x)
    for cell in needs_refine:
        v0, v1 = cells[cell].pop()
        x0, x1 = x[v0], x[v1]
        l = np.linalg.norm(x0 - x1)

        nodes = [v0]
        
        ts = np.linspace(0., 1., int(ceil(l/threshold))+1)[1:-1]
        dx = x1 - x0
        for t in ts:
            xmid = x0 + t*dx
            
            x = np.row_stack([x, xmid])
            
            nodes.append(next_v)
            next_v += 1

        nodes.append(v1)

        cells[cell] = list(zip(nodes[:-1], nodes[1:]))

    

    # Mapping for 
    parent_cell_map = sum(([k]*len(cells[k]) for k in sorted(cells)), [])

    cells = np.array(sum((cells[k] for k in sorted(cells)), []), dtype='uintp')
    mesh = make_line_mesh(x, cells)

    return mesh, np.array(parent_cell_map, dtype='uintp')
    
# --------------------------------------------------------------------

if __name__ == '__main__':
    coords = np.array([[0, 0], [1, 0], [1, 0.2], [1, 0.5], [1, 0.7], [1, 1], [0, 1.]])
    mesh = make_line_mesh(coords, close_path=True)

    rmesh, mapping = refine(mesh, threshold=0.6)

    x = mesh.coordinates()
    y = rmesh.coordinates()
    assert np.linalg.norm(x - y[:len(x)]) < 1E-13

    e2v, E2V = mesh.topology()(1, 0), rmesh.topology()(1, 0)
    for c in range(mesh.num_cells()):
        x0, x1 = x[e2v(c)]
        e = x1 - x0
        e = e/np.linalg.norm(e)

        for C in np.where(mapping == c)[0]:
            y0, y1 = y[E2V(C)]
            E = y1 - y0
            E = E/np.linalg.norm(E)

            assert abs(1-abs(np.dot(e, E))) < 1E-13
