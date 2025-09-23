# RESULTS

## test_fact_persistence_regular()

```json
{
  "0": {
    "A": {},
    "B": {},
    "C": {},
    "A,B": {"connected": [1.0, 1.0]},
    "B,C": {"connected": [1.0, 1.0]},
    "A,C": {}
  },
  "1": {
    "A": {},
    "B": {},
    "C": {},
    "A,B": {},
    "B,C": {},
    "A,C": {"connected": [1.0, 1.0]}
  }
}
```

Querying with `return_bool=False` to see bounds:
```
connected(A, B) bounds: (0, 0)
connected(B, C) bounds: (0, 0)
connected(A, C) bounds: (1.0, 1.0)
```

## test_fact_persistence_fp()
```json
{
  "0": {
    "A": {},
    "B": {},
    "C": {},
    "A,B": {"connected": [1.0, 1.0]},
    "B,C": {"connected": [1.0, 1.0]},
    "A,C": {}
  },
  "1": {
    "A": {},
    "B": {},
    "C": {},
    "A,B": {},
    "B,C": {},
    "A,C": {"connected": [1.0, 1.0]}
  },
  "2": {
    "A": {},
    "B": {},
    "C": {},
    "A,B": {},
    "B,C": {},
    "A,C": {}
  }
}
```

```
connected(A, B) bounds: (1.0, 1.0)
connected(B, C) bounds: (1.0, 1.0)
connected(A, C) bounds: (0, 0)
```

**NOTE**: This dict has an empty set of values for timestep 2 not seen in the regular version (both with timesteps=2). Other than that, it looks like it's just a discrepancy with the query method.

## test_transitive_with_more_edges()

### Regular results with multiple edges:
```
  connected(A, B): False
  connected(B, C): False
  connected(C, D): False
  connected(A, D): False
```

```json
{
  "0": {
    "A": {},
    "B": {},
    "C": {},
    "D": {},
    "E": {},
    "A,B": {"connected": [1.0, 1.0]},
    "B,C": {"connected": [1.0, 1.0]},
    "C,D": {"connected": [1.0, 1.0]},
    "D,E": {"connected": [1.0, 1.0]},
    "A,C": {},
    "B,D": {},
    "C,E": {},
    "A,E": {}
  },
  "1": {
    "A": {},
    "B": {},
    "C": {},
    "D": {},
    "E": {},
    "A,B": {},
    "B,C": {},
    "C,D": {},
    "D,E": {},
    "A,C": {"connected": [1.0, 1.0]},
    "B,D": {"connected": [1.0, 1.0]},
    "C,E": {"connected": [1.0, 1.0]},
    "A,E": {}
  },
  "2": {
    "A": {},
    "B": {},
    "C": {},
    "D": {},
    "E": {},
    "A,B": {},
    "B,C": {},
    "C,D": {},
    "D,E": {},
    "A,C": {},
    "B,D": {},
    "C,E": {},
    "A,E": {"connected": [1.0, 1.0]}
  }
}
```

### FP results with multiple edges:
```
connected(A, B): True
connected(B, C): True
connected(C, D): True
connected(A, D): False
```

```json
{
  "0": {
    "A": {},
    "B": {},
    "C": {},
    "D": {},
    "E": {},
    "A,B": {"connected": [1.0, 1.0]},
    "B,C": {"connected": [1.0, 1.0]},
    "C,D": {"connected": [1.0, 1.0]},
    "D,E": {"connected": [1.0, 1.0]},
    "A,C": {},
    "B,D": {},
    "C,E": {},
    "A,E": {}
  },
  "1": {
    "A": {},
    "B": {},
    "C": {},
    "D": {},
    "E": {},
    "A,B": {},
    "B,C": {},
    "C,D": {},
    "D,E": {},
    "A,C": {"connected": [1.0, 1.0]},
    "B,D": {"connected": [1.0, 1.0]},
    "C,E": {"connected": [1.0, 1.0]},
    "A,E": {}
  },
  "2": {
    "A": {},
    "B": {},
    "C": {},
    "D": {},
    "E": {},
    "A,B": {},
    "B,C": {},
    "C,D": {},
    "D,E": {},
    "A,C": {},
    "B,D": {},
    "C,E": {},
    "A,E": {"connected": [1.0, 1.0]}
  },
  "3": {
    "A": {},
    "B": {},
    "C": {},
    "D": {},
    "E": {},
    "A,B": {},
    "B,C": {},
    "C,D": {},
    "D,E": {},
    "A,C": {},
    "B,D": {},
    "C,E": {},
    "A,E": {}
  }
}
```

## CASE 1

### Regular results:
```
connected(A, C): True
connected(X, Y): False
```

```json
{
    "0": {
        "A": {},
        "B": {},
        "C": {},
        "X": {},
        "Y": {},
        "('A', 'B')": {
            "connected": [1.0, 1.0]
        },
        "('B', 'C')": {
            "connected": [1.0, 1.0]
        },
        "('X', 'Y')": {
            "connected": [1.0, 1.0]
        },
        "('A', 'C')": {}
    },
    "1": {
        "A": {},
        "B": {},
        "C": {},
        "X": {},
        "Y": {},
        "('A', 'B')": {},
        "('B', 'C')": {},
        "('X', 'Y')": {},
        "('A', 'C')": {
            "connected": [1.0, 1.0]
        }
    }
}
```

### FP Results:
```
connected(A, C): False
connected(X, Y): True
```

```json
{
    "0": {
        "A": {},
        "B": {},
        "C": {},
        "X": {},
        "Y": {},
        "('A', 'B')": { "connected": [1.0, 1.0] },
        "('B', 'C')": { "connected": [1.0, 1.0] },
        "('X', 'Y')": { "connected": [1.0, 1.0] },
        "('A', 'C')": {}
    },
    "1": {
        "A": {},
        "B": {},
        "C": {},
        "X": {},
        "Y": {},
        "('A', 'B')": {},
        "('B', 'C')": {},
        "('X', 'Y')": {},
        "('A', 'C')": { "connected": [1.0, 1.0] }
    },
    "2": {
        "A": {},
        "B": {},
        "C": {},
        "X": {},
        "Y": {},
        "('A', 'B')": {},
        "('B', 'C')": {},
        "('X', 'Y')": {},
        "('A', 'C')": {}
    }
}