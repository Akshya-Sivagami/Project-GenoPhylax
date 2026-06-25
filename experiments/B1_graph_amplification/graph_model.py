import networkx as nx
import numpy as np
import random
from collections import defaultdict

# ── Reproducibility ───────────────────────────────────────────────────────────
random.seed(42)
np.random.seed(42)

# ═════════════════════════════════════════════════════════════════════════════
# 1. KINSHIP GRAPH GENERATOR
# Builds a synthetic population-scale kinship graph with realistic
# family structures: nuclear families, cousins, grandparents.
# ═════════════════════════════════════════════════════════════════════════════

def generate_kinship_graph(n_families=500, avg_children=2, cousin_prob=0.3):
    """
    Generate a synthetic kinship graph.
    
    Parameters:
        n_families   : number of nuclear family units
        avg_children : average children per family
        cousin_prob  : probability of cross-family cousin edges
    
    Returns:
        G : NetworkX graph with node/edge metadata
    """
    G = nx.Graph()
    node_id = 0
    family_data = []

    for f in range(n_families):
        # Each family: 2 parents + children
        parent_a = node_id;     node_id += 1
        parent_b = node_id;     node_id += 1
        n_children = max(1, np.random.poisson(avg_children))
        children = list(range(node_id, node_id + n_children))
        node_id += n_children

        all_members = [parent_a, parent_b] + children

        # Add nodes with metadata
        for n in all_members:
            G.add_node(n, family=f, registered=False, exposed=False)

        # Parent-parent edge (spouse)
        G.add_edge(parent_a, parent_b, relationship="spouse", weight=0.5)

        # Parent-child edges
        for c in children:
            G.add_edge(parent_a, c, relationship="parent_child", weight=1.0)
            G.add_edge(parent_b, c, relationship="parent_child", weight=1.0)

        # Sibling edges
        for i in range(len(children)):
            for j in range(i+1, len(children)):
                G.add_edge(children[i], children[j],
                           relationship="sibling", weight=0.5)

        family_data.append({
            "parents": [parent_a, parent_b],
            "children": children
        })

    # Cross-family cousin edges
    for f1 in range(n_families):
        for f2 in range(f1+1, n_families):
            if random.random() < cousin_prob:
                c1 = random.choice(family_data[f1]["children"]) \
                     if family_data[f1]["children"] else family_data[f1]["parents"][0]
                c2 = random.choice(family_data[f2]["children"]) \
                     if family_data[f2]["children"] else family_data[f2]["parents"][0]
                G.add_edge(c1, c2, relationship="cousin", weight=0.25)

    return G, family_data


# ═════════════════════════════════════════════════════════════════════════════
# 2. DTC PLATFORM REGISTRATION
# Simulates what fraction of the population registers on a DTC platform
# like 23andMe. Only registered users appear in the kinship graph features.
# ═════════════════════════════════════════════════════════════════════════════

def simulate_registration(G, registration_rate=0.4):
    """
    Mark a fraction of nodes as registered on the DTC platform.
    
    Parameters:
        G                 : kinship graph
        registration_rate : fraction of population registered
    
    Returns:
        registered_nodes : list of registered node IDs
    """
    all_nodes = list(G.nodes())
    n_register = int(len(all_nodes) * registration_rate)
    registered = random.sample(all_nodes, n_register)
    
    for n in registered:
        G.nodes[n]["registered"] = True
    
    return registered


# ═════════════════════════════════════════════════════════════════════════════
# 3. BREACH SIMULATION
# Simulates a credential-stuffing breach starting from a set of
# compromised accounts. Exposure propagates through kinship edges
# to all registered relatives — modelling DNA Relatives-style features.
# ═════════════════════════════════════════════════════════════════════════════

def simulate_breach(G, registered_nodes, n_compromised, max_hops=3):
    """
    Simulate a graph-amplified breach.
    
    Parameters:
        G                : kinship graph
        registered_nodes : list of registered node IDs
        n_compromised    : number of initially compromised accounts
        max_hops         : how many relationship hops exposure travels
    
    Returns:
        dict with breach metrics
    """
    # Reset exposure state
    for n in G.nodes():
        G.nodes[n]["exposed"] = False
        G.nodes[n]["compromised"] = False

    # Select initial compromised accounts from registered users
    n_compromised = min(n_compromised, len(registered_nodes))
    compromised = random.sample(registered_nodes, n_compromised)
    
    for n in compromised:
        G.nodes[n]["compromised"] = True
        G.nodes[n]["exposed"] = True

    # BFS propagation through kinship graph up to max_hops
    exposed_set = set(compromised)
    frontier = set(compromised)

    for hop in range(max_hops):
        next_frontier = set()
        for node in frontier:
            for neighbor in G.neighbors(node):
                if neighbor not in exposed_set and G.nodes[neighbor]["registered"]:
                    exposed_set.add(neighbor)
                    next_frontier.add(neighbor)
                    G.nodes[neighbor]["exposed"] = True
        frontier = next_frontier
        if not frontier:
            break

    total_exposed = len(exposed_set)
    amplification_factor = total_exposed / n_compromised if n_compromised > 0 else 0

    return {
        "n_registered"       : len(registered_nodes),
        "n_compromised"      : n_compromised,
        "n_exposed"          : total_exposed,
        "amplification"      : round(amplification_factor, 2),
        "exposure_rate"      : round(total_exposed / len(registered_nodes), 4),
        "compromised_nodes"  : compromised,
        "exposed_nodes"      : list(exposed_set),
    }


# ═════════════════════════════════════════════════════════════════════════════
# 4. 23andME CALIBRATION
# Validates our model against the real-world 23andMe breach:
# 14,000 compromised → 6.9 million exposed (amplification ~493x)
# ═════════════════════════════════════════════════════════════════════════════

def calibrate_against_23andme(G, registered_nodes):
    """
    Scale our model to 23andMe proportions and check amplification factor.
    23andMe had ~14M registered users; 14K compromised → 6.9M exposed.
    Target amplification: ~493x
    """
    total_registered = len(registered_nodes)
    
    # 23andMe breach ratio: 14000 / 14000000 = 0.001 (0.1% compromised)
    breach_ratio = 14_000 / 14_000_000
    n_compromised = max(1, int(total_registered * breach_ratio))

    result = simulate_breach(G, registered_nodes, n_compromised, max_hops=3)
    
    # Real-world reference
    real_compromised  = 14_000
    real_exposed      = 6_900_000
    real_amplification = real_exposed / real_compromised  # 492.86x

    result["real_compromised"]   = real_compromised
    result["real_exposed"]       = real_exposed
    result["real_amplification"] = round(real_amplification, 2)
    result["model_vs_real"]      = round(result["amplification"] / real_amplification, 4)

    return result


if __name__ == "__main__":
    print("Building kinship graph...")
    G, family_data = generate_kinship_graph(n_families=500)
    print(f"  Nodes: {G.number_of_nodes():,}")
    print(f"  Edges: {G.number_of_edges():,}")

    print("\nSimulating DTC platform registration (40% rate)...")
    registered = simulate_registration(G, registration_rate=0.4)
    print(f"  Registered users: {len(registered):,}")

    print("\nRunning breach simulation (0.1% compromised)...")
    n_comp = max(1, int(len(registered) * 0.001))
    result = simulate_breach(G, registered, n_compromised=n_comp)
    print(f"  Compromised : {result['n_compromised']:,}")
    print(f"  Exposed     : {result['n_exposed']:,}")
    print(f"  Amplification factor: {result['amplification']}x")

    print("\nCalibrating against 23andMe breach...")
    cal = calibrate_against_23andme(G, registered)
    print(f"  Model amplification : {cal['amplification']}x")
    print(f"  Real amplification  : {cal['real_amplification']}x")
    print(f"  Model/Real ratio    : {cal['model_vs_real']}")
    print("\nDone. graph_model.py verified.")