"""Reviewed placement data; every delta is pinned to its general-planner input."""
import json

PLAN = json.loads(r'''
{
  "103": {
    "input_unit_sha256": "26bb087702abcaaa97e002ab78e7331cea7a2de2a7050afd70ddb31b277df9c4",
    "moves": [
      {
        "index": 17,
        "before": [
          1312,
          496,
          178,
          11
        ],
        "after": [
          1120,
          496,
          178,
          11
        ]
      },
      {
        "index": 18,
        "before": [
          832,
          752,
          177,
          11
        ],
        "after": [
          1184,
          496,
          177,
          11
        ]
      },
      {
        "index": 19,
        "before": [
          1600,
          656,
          177,
          11
        ],
        "after": [
          1568,
          560,
          177,
          11
        ]
      },
      {
        "index": 20,
        "before": [
          1536,
          560,
          176,
          11
        ],
        "after": [
          1504,
          496,
          176,
          11
        ]
      },
      {
        "index": 21,
        "before": [
          1504,
          528,
          178,
          11
        ],
        "after": [
          1440,
          464,
          178,
          11
        ]
      },
      {
        "index": 22,
        "before": [
          832,
          784,
          178,
          11
        ],
        "after": [
          1152,
          528,
          178,
          11
        ]
      },
      {
        "index": 23,
        "before": [
          832,
          720,
          176,
          11
        ],
        "after": [
          1248,
          496,
          176,
          11
        ]
      },
      {
        "index": 24,
        "before": [
          1376,
          528,
          177,
          11
        ],
        "after": [
          1312,
          496,
          177,
          11
        ]
      },
      {
        "index": 27,
        "before": [
          832,
          816,
          176,
          11
        ],
        "after": [
          1120,
          560,
          176,
          11
        ]
      },
      {
        "index": 60,
        "before": [
          1088,
          848,
          178,
          11
        ],
        "after": [
          1088,
          656,
          178,
          11
        ]
      },
      {
        "index": 64,
        "before": [
          1024,
          848,
          176,
          11
        ],
        "after": [
          1088,
          688,
          176,
          11
        ]
      },
      {
        "index": 65,
        "before": [
          960,
          848,
          176,
          11
        ],
        "after": [
          1088,
          624,
          176,
          11
        ]
      },
      {
        "index": 66,
        "before": [
          1536,
          688,
          177,
          11
        ],
        "after": [
          1536,
          528,
          177,
          11
        ]
      },
      {
        "index": 69,
        "before": [
          1440,
          528,
          178,
          11
        ],
        "after": [
          1376,
          464,
          178,
          11
        ]
      },
      {
        "index": 70,
        "before": [
          896,
          848,
          176,
          11
        ],
        "after": [
          1120,
          592,
          176,
          11
        ]
      }
    ],
    "groups": [
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 160,
          "center": [
            320,
            2704
          ],
          "depot_type": 106,
          "owner": 1,
          "top_left_tile": [
            8,
            83
          ]
        },
        "mineral_indices": [
          147,
          143,
          151,
          152,
          154,
          145,
          149,
          155,
          146,
          144
        ],
        "gas_indices": [
          166
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 3
        },
        "parent_site_index": 0,
        "group_index": 0,
        "group_sizes": [
          10
        ],
        "source_anchor": [
          320,
          2704
        ],
        "planned_depot_sites": [],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 188,
          "center": [
            1344,
            688
          ],
          "depot_type": 131,
          "owner": 4,
          "top_left_tile": [
            40,
            20
          ]
        },
        "mineral_indices": [
          24,
          17,
          69,
          66,
          20,
          19,
          21,
          22,
          27,
          70,
          60,
          64,
          18,
          23,
          65
        ],
        "gas_indices": [
          35
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 20,
          "plateau": 12,
          "depot_clearance": 72
        },
        "parent_site_index": 1,
        "group_index": 0,
        "group_sizes": [
          15
        ],
        "source_anchor": [
          1344,
          688
        ],
        "planned_depot_sites": [],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "maximum_minerals": 15,
        "placement_policy": "reviewed_playtest_layout"
      }
    ]
  },
  "105": {
    "input_unit_sha256": "e878772abfa302278bf7169cd38c559e4940a9eeb076112591bf79163e8d4a13",
    "moves": [
      {
        "index": 79,
        "before": [
          2912,
          2512,
          176,
          11
        ],
        "after": [
          2816,
          2032,
          176,
          11
        ]
      },
      {
        "index": 80,
        "before": [
          2656,
          2672,
          178,
          11
        ],
        "after": [
          2432,
          2096,
          178,
          11
        ]
      },
      {
        "index": 81,
        "before": [
          2464,
          2000,
          177,
          11
        ],
        "after": [
          2432,
          1872,
          177,
          11
        ]
      },
      {
        "index": 82,
        "before": [
          2464,
          2032,
          176,
          11
        ],
        "after": [
          2432,
          1904,
          176,
          11
        ]
      },
      {
        "index": 83,
        "before": [
          2464,
          2064,
          178,
          11
        ],
        "after": [
          2432,
          1936,
          178,
          11
        ]
      },
      {
        "index": 103,
        "before": [
          2720,
          2096,
          178,
          11
        ],
        "after": [
          2432,
          2000,
          178,
          11
        ]
      },
      {
        "index": 106,
        "before": [
          2720,
          2672,
          178,
          11
        ],
        "after": [
          2464,
          2128,
          178,
          11
        ]
      },
      {
        "index": 107,
        "before": [
          2528,
          2096,
          178,
          11
        ],
        "after": [
          2432,
          1968,
          178,
          11
        ]
      },
      {
        "index": 112,
        "before": [
          2784,
          2672,
          177,
          11
        ],
        "after": [
          2528,
          2128,
          177,
          11
        ]
      },
      {
        "index": 113,
        "before": [
          2848,
          2672,
          177,
          11
        ],
        "after": [
          2592,
          2128,
          177,
          11
        ]
      },
      {
        "index": 118,
        "before": [
          2912,
          2608,
          176,
          11
        ],
        "after": [
          2720,
          2128,
          176,
          11
        ]
      },
      {
        "index": 119,
        "before": [
          2592,
          2096,
          178,
          11
        ],
        "after": [
          2432,
          2064,
          178,
          11
        ]
      },
      {
        "index": 120,
        "before": [
          2432,
          1888,
          110,
          6
        ],
        "after": [
          2336,
          1728,
          110,
          6
        ]
      },
      {
        "index": 123,
        "before": [
          2912,
          2544,
          177,
          11
        ],
        "after": [
          2784,
          2128,
          177,
          11
        ]
      },
      {
        "index": 128,
        "before": [
          2656,
          2096,
          178,
          11
        ],
        "after": [
          2432,
          2032,
          178,
          11
        ]
      },
      {
        "index": 129,
        "before": [
          2912,
          2576,
          178,
          11
        ],
        "after": [
          2656,
          2128,
          178,
          11
        ]
      }
    ],
    "groups": [
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 36,
          "center": [
            2720,
            464
          ],
          "depot_type": 106,
          "owner": 3,
          "top_left_tile": [
            83,
            13
          ]
        },
        "mineral_indices": [
          14,
          12,
          9,
          21,
          8,
          23,
          2,
          22
        ],
        "gas_indices": [
          28,
          187
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 4,
          "resource_overlap": 3,
          "gas_exit": 2
        },
        "parent_site_index": 0,
        "group_index": 0,
        "group_sizes": [
          8,
          9
        ],
        "source_anchor": [
          2720,
          464
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              2784,
              144
            ],
            "depot_type": 106,
            "owner": 3,
            "top_left_tile": [
              85,
              3
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              2624,
              1968
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              80,
              60
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            2784,
            144
          ],
          "depot_type": 106,
          "owner": 3,
          "top_left_tile": [
            85,
            3
          ],
          "additional_group_depot": true
        },
        "mineral_indices": [
          1,
          18,
          5,
          0,
          6,
          7,
          10,
          11,
          15
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 35,
          "geometry": 11,
          "depot_clearance": 14
        },
        "parent_site_index": 0,
        "group_index": 1,
        "group_sizes": [
          8,
          9
        ],
        "source_anchor": [
          2720,
          464
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              2784,
              144
            ],
            "depot_type": 106,
            "owner": 3,
            "top_left_tile": [
              85,
              3
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              2624,
              1968
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              80,
              60
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            2624,
            1968
          ],
          "depot_type": 106,
          "owner": null,
          "top_left_tile": [
            80,
            60
          ]
        },
        "mineral_indices": [
          119,
          128,
          81,
          82,
          83,
          103,
          107,
          113,
          118,
          129,
          112,
          123,
          106,
          80,
          79
        ],
        "gas_indices": [
          120
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 1,
          "geometry": 1
        },
        "parent_site_index": 1,
        "group_index": 0,
        "group_sizes": [
          15
        ],
        "source_anchor": [
          2656,
          1936
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              2784,
              144
            ],
            "depot_type": 106,
            "owner": 3,
            "top_left_tile": [
              85,
              3
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              2624,
              1968
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              80,
              60
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "maximum_minerals": 15,
        "placement_policy": "reviewed_playtest_layout"
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 140,
          "center": [
            256,
            2768
          ],
          "depot_type": 106,
          "owner": 6,
          "top_left_tile": [
            6,
            85
          ]
        },
        "mineral_indices": [
          133,
          125,
          104,
          108,
          111,
          109,
          122,
          115,
          116
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 46
        },
        "parent_site_index": 2,
        "group_index": 0,
        "group_sizes": [
          9
        ],
        "source_anchor": [
          256,
          2768
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              2784,
              144
            ],
            "depot_type": 106,
            "owner": 3,
            "top_left_tile": [
              85,
              3
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              2624,
              1968
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              80,
              60
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      }
    ]
  },
  "108": {
    "input_unit_sha256": "e581c5484634a26b7eda107329a8818214bbcc2106dd9785f09cf23bebee183f",
    "moves": [
      {
        "index": 239,
        "before": [
          2784,
          3296,
          108,
          11
        ],
        "after": [
          2688,
          3296,
          108,
          11
        ]
      },
      {
        "index": 241,
        "before": [
          2752,
          3424,
          115,
          11
        ],
        "after": [
          2880,
          3296,
          115,
          11
        ]
      },
      {
        "index": 256,
        "before": [
          2080,
          3584,
          108,
          11
        ],
        "after": [
          1920,
          3552,
          108,
          11
        ]
      },
      {
        "index": 262,
        "before": [
          2048,
          3456,
          188,
          11
        ],
        "after": [
          2048,
          3360,
          188,
          11
        ]
      }
    ],
    "groups": [
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 157,
          "center": [
            1376,
            2096
          ],
          "depot_type": 106,
          "owner": 5,
          "top_left_tile": [
            41,
            64
          ]
        },
        "mineral_indices": [
          144,
          137,
          139,
          125,
          126,
          130,
          133,
          140,
          132
        ],
        "gas_indices": [
          121
        ],
        "status": "ladder_separate_gas",
        "reasons": {},
        "parent_site_index": 0,
        "group_index": 0,
        "group_sizes": [
          9,
          10
        ],
        "source_anchor": [
          1376,
          2096
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              1248,
              2416
            ],
            "depot_type": 106,
            "owner": 5,
            "top_left_tile": [
              37,
              74
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1824,
              3536
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              55,
              109
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2592,
              3280
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              79,
              101
            ]
          },
          {
            "kind": "expansion",
            "center": [
              192,
              592
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              4,
              17
            ]
          },
          {
            "kind": "expansion",
            "center": [
              576,
              592
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              16,
              17
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              576,
              272
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              16,
              7
            ],
            "additional_group_depot": true
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            1248,
            2416
          ],
          "depot_type": 106,
          "owner": 5,
          "top_left_tile": [
            37,
            74
          ],
          "additional_group_depot": true
        },
        "mineral_indices": [
          152,
          156,
          151,
          150,
          145,
          143,
          138,
          127,
          131,
          124
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 28
        },
        "parent_site_index": 0,
        "group_index": 1,
        "group_sizes": [
          9,
          10
        ],
        "source_anchor": [
          1376,
          2096
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              1248,
              2416
            ],
            "depot_type": 106,
            "owner": 5,
            "top_left_tile": [
              37,
              74
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1824,
              3536
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              55,
              109
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2592,
              3280
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              79,
              101
            ]
          },
          {
            "kind": "expansion",
            "center": [
              192,
              592
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              4,
              17
            ]
          },
          {
            "kind": "expansion",
            "center": [
              576,
              592
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              16,
              17
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              576,
              272
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              16,
              7
            ],
            "additional_group_depot": true
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 55,
          "center": [
            3456,
            816
          ],
          "depot_type": 106,
          "owner": 4,
          "top_left_tile": [
            106,
            24
          ]
        },
        "mineral_indices": [
          45,
          47,
          46,
          49,
          44,
          42,
          50,
          41,
          40,
          43,
          48
        ],
        "gas_indices": [
          69
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 56
        },
        "parent_site_index": 1,
        "group_index": 0,
        "group_sizes": [
          11
        ],
        "source_anchor": [
          3456,
          816
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              1248,
              2416
            ],
            "depot_type": 106,
            "owner": 5,
            "top_left_tile": [
              37,
              74
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1824,
              3536
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              55,
              109
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2592,
              3280
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              79,
              101
            ]
          },
          {
            "kind": "expansion",
            "center": [
              192,
              592
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              4,
              17
            ]
          },
          {
            "kind": "expansion",
            "center": [
              576,
              592
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              16,
              17
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              576,
              272
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              16,
              7
            ],
            "additional_group_depot": true
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            1824,
            3536
          ],
          "depot_type": 106,
          "owner": null,
          "top_left_tile": [
            55,
            109
          ]
        },
        "mineral_indices": [
          251,
          249,
          252,
          246,
          245,
          244,
          254,
          255,
          243,
          247,
          240
        ],
        "gas_indices": [
          262
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 8,
          "geometry": 5,
          "army_route": 42,
          "gas_lane": 4,
          "gas_inside_bank": 3
        },
        "parent_site_index": 2,
        "group_index": 0,
        "group_sizes": [
          11
        ],
        "source_anchor": [
          1824,
          3536
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              1248,
              2416
            ],
            "depot_type": 106,
            "owner": 5,
            "top_left_tile": [
              37,
              74
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1824,
              3536
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              55,
              109
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2592,
              3280
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              79,
              101
            ]
          },
          {
            "kind": "expansion",
            "center": [
              192,
              592
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              4,
              17
            ]
          },
          {
            "kind": "expansion",
            "center": [
              576,
              592
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              16,
              17
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              576,
              272
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              16,
              7
            ],
            "additional_group_depot": true
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            2592,
            3280
          ],
          "depot_type": 106,
          "owner": null,
          "top_left_tile": [
            79,
            101
          ]
        },
        "mineral_indices": [
          230,
          223,
          234,
          233,
          224,
          232,
          227,
          235,
          226,
          229
        ],
        "gas_indices": [
          322,
          323
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 2,
          "resource_overlap": 18
        },
        "parent_site_index": 3,
        "group_index": 0,
        "group_sizes": [
          10
        ],
        "source_anchor": [
          2592,
          3280
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              1248,
              2416
            ],
            "depot_type": 106,
            "owner": 5,
            "top_left_tile": [
              37,
              74
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1824,
              3536
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              55,
              109
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2592,
              3280
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              79,
              101
            ]
          },
          {
            "kind": "expansion",
            "center": [
              192,
              592
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              4,
              17
            ]
          },
          {
            "kind": "expansion",
            "center": [
              576,
              592
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              16,
              17
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              576,
              272
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              16,
              7
            ],
            "additional_group_depot": true
          }
        ],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            192,
            592
          ],
          "depot_type": 106,
          "owner": null,
          "top_left_tile": [
            4,
            17
          ]
        },
        "mineral_indices": [
          1,
          2,
          5,
          4,
          31,
          36,
          30,
          25
        ],
        "gas_indices": [
          7
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 3,
          "plateau": 6,
          "gas_lane": 1
        },
        "parent_site_index": 4,
        "group_index": 0,
        "group_sizes": [
          8,
          8,
          9
        ],
        "source_anchor": [
          192,
          592
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              1248,
              2416
            ],
            "depot_type": 106,
            "owner": 5,
            "top_left_tile": [
              37,
              74
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1824,
              3536
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              55,
              109
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2592,
              3280
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              79,
              101
            ]
          },
          {
            "kind": "expansion",
            "center": [
              192,
              592
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              4,
              17
            ]
          },
          {
            "kind": "expansion",
            "center": [
              576,
              592
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              16,
              17
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              576,
              272
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              16,
              7
            ],
            "additional_group_depot": true
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            576,
            592
          ],
          "depot_type": 106,
          "owner": null,
          "top_left_tile": [
            16,
            17
          ],
          "additional_group_depot": true
        },
        "mineral_indices": [
          26,
          17,
          24,
          15,
          18,
          3,
          32,
          29
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 1
        },
        "parent_site_index": 4,
        "group_index": 1,
        "group_sizes": [
          8,
          8,
          9
        ],
        "source_anchor": [
          192,
          592
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              1248,
              2416
            ],
            "depot_type": 106,
            "owner": 5,
            "top_left_tile": [
              37,
              74
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1824,
              3536
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              55,
              109
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2592,
              3280
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              79,
              101
            ]
          },
          {
            "kind": "expansion",
            "center": [
              192,
              592
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              4,
              17
            ]
          },
          {
            "kind": "expansion",
            "center": [
              576,
              592
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              16,
              17
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              576,
              272
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              16,
              7
            ],
            "additional_group_depot": true
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            576,
            272
          ],
          "depot_type": 106,
          "owner": null,
          "top_left_tile": [
            16,
            7
          ],
          "additional_group_depot": true
        },
        "mineral_indices": [
          11,
          14,
          23,
          0,
          34,
          33,
          38,
          35,
          37
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 1
        },
        "parent_site_index": 4,
        "group_index": 2,
        "group_sizes": [
          8,
          8,
          9
        ],
        "source_anchor": [
          192,
          592
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              1248,
              2416
            ],
            "depot_type": 106,
            "owner": 5,
            "top_left_tile": [
              37,
              74
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1824,
              3536
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              55,
              109
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2592,
              3280
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              79,
              101
            ]
          },
          {
            "kind": "expansion",
            "center": [
              192,
              592
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              4,
              17
            ]
          },
          {
            "kind": "expansion",
            "center": [
              576,
              592
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              16,
              17
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              576,
              272
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              16,
              7
            ],
            "additional_group_depot": true
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      }
    ]
  },
  "109": {
    "input_unit_sha256": "b2fc04696d18e88afd49147ada452452d1c7b3bb4f519fb11ee70be3bbca94c2",
    "moves": [
      {
        "index": 109,
        "before": [
          1056,
          336,
          178,
          11
        ],
        "after": [
          736,
          720,
          178,
          11
        ]
      },
      {
        "index": 111,
        "before": [
          992,
          336,
          178,
          11
        ],
        "after": [
          672,
          688,
          178,
          11
        ]
      },
      {
        "index": 118,
        "before": [
          992,
          496,
          178,
          11
        ],
        "after": [
          672,
          464,
          178,
          11
        ]
      },
      {
        "index": 123,
        "before": [
          992,
          528,
          177,
          11
        ],
        "after": [
          672,
          496,
          177,
          11
        ]
      },
      {
        "index": 148,
        "before": [
          992,
          368,
          176,
          11
        ],
        "after": [
          672,
          624,
          176,
          11
        ]
      },
      {
        "index": 149,
        "before": [
          992,
          432,
          176,
          11
        ],
        "after": [
          672,
          560,
          176,
          11
        ]
      },
      {
        "index": 150,
        "before": [
          928,
          368,
          176,
          11
        ],
        "after": [
          672,
          656,
          176,
          11
        ]
      },
      {
        "index": 152,
        "before": [
          992,
          400,
          176,
          11
        ],
        "after": [
          672,
          592,
          176,
          11
        ]
      },
      {
        "index": 153,
        "before": [
          992,
          464,
          176,
          11
        ],
        "after": [
          672,
          528,
          176,
          11
        ]
      }
    ],
    "groups": [
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 242,
          "center": [
            96,
            208
          ],
          "depot_type": 133,
          "owner": 3,
          "top_left_tile": [
            1,
            5
          ]
        },
        "mineral_indices": [
          28,
          40,
          13,
          49,
          12,
          50,
          39,
          38,
          14,
          27,
          29
        ],
        "gas_indices": [
          83
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 13,
          "plateau": 47,
          "gas_lane": 226,
          "gas_exit": 2,
          "gas_inside_bank": 20
        },
        "parent_site_index": 0,
        "group_index": 0,
        "group_sizes": [
          11
        ],
        "source_anchor": [
          96,
          208
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              864,
              560
            ],
            "depot_type": 106,
            "owner": 0,
            "top_left_tile": [
              25,
              16
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              160,
              1904
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              3,
              58
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2176,
              2736
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              66,
              84
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 124,
          "center": [
            1056,
            720
          ],
          "depot_type": 106,
          "owner": 0,
          "top_left_tile": [
            31,
            21
          ]
        },
        "mineral_indices": [
          119,
          115,
          157,
          114,
          155,
          156,
          139,
          127,
          133
        ],
        "gas_indices": [
          120,
          289
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 2,
          "resource_overlap": 2
        },
        "parent_site_index": 1,
        "group_index": 0,
        "group_sizes": [
          9,
          9
        ],
        "source_anchor": [
          1056,
          720
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              864,
              560
            ],
            "depot_type": 106,
            "owner": 0,
            "top_left_tile": [
              25,
              16
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              160,
              1904
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              3,
              58
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2176,
              2736
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              66,
              84
            ]
          }
        ],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "sunken_avoidance": {
          "hostile_owners": [
            3
          ],
          "unit_id": 146,
          "weapon_id": 53,
          "range_pixels": 224,
          "margin_pixels": 32,
          "worker_envelope_pixels": 32,
          "units_sha256": "da2ee6f116b77329048ec6be9e02721a527fde23d4b05b1b1336e634490abcba",
          "weapons_sha256": "80de165015519f9bed46ea8858195c2d2d0120b65b9e55e1c0a50b19135f4b62"
        },
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            864,
            560
          ],
          "depot_type": 106,
          "owner": 0,
          "top_left_tile": [
            25,
            16
          ],
          "additional_group_depot": true
        },
        "mineral_indices": [
          109,
          111,
          150,
          148,
          152,
          149,
          153,
          123,
          118
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 27,
          "geometry": 13,
          "army_route": 5,
          "depot_clearance": 12
        },
        "parent_site_index": 1,
        "group_index": 1,
        "group_sizes": [
          9,
          9
        ],
        "source_anchor": [
          1056,
          720
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              864,
              560
            ],
            "depot_type": 106,
            "owner": 0,
            "top_left_tile": [
              25,
              16
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              160,
              1904
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              3,
              58
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2176,
              2736
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              66,
              84
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "sunken_avoidance": {
          "hostile_owners": [
            3
          ],
          "unit_id": 146,
          "weapon_id": 53,
          "range_pixels": 224,
          "margin_pixels": 32,
          "worker_envelope_pixels": 32,
          "units_sha256": "da2ee6f116b77329048ec6be9e02721a527fde23d4b05b1b1336e634490abcba",
          "weapons_sha256": "80de165015519f9bed46ea8858195c2d2d0120b65b9e55e1c0a50b19135f4b62"
        },
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 212,
          "center": [
            3584,
            2832
          ],
          "depot_type": 154,
          "owner": 1,
          "top_left_tile": [
            110,
            87
          ]
        },
        "mineral_indices": [
          217,
          221,
          230,
          226,
          227,
          220,
          228,
          216,
          231,
          232
        ],
        "gas_indices": [
          205
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 33,
          "geometry": 20,
          "gas_lane": 4
        },
        "parent_site_index": 2,
        "group_index": 0,
        "group_sizes": [
          10
        ],
        "source_anchor": [
          3584,
          2832
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              864,
              560
            ],
            "depot_type": 106,
            "owner": 0,
            "top_left_tile": [
              25,
              16
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              160,
              1904
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              3,
              58
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2176,
              2736
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              66,
              84
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 66,
          "center": [
            3744,
            208
          ],
          "depot_type": 154,
          "owner": 1,
          "top_left_tile": [
            115,
            5
          ]
        },
        "mineral_indices": [
          10,
          15,
          41,
          30,
          42,
          26,
          52,
          11,
          25
        ],
        "gas_indices": [
          86
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 37
        },
        "parent_site_index": 3,
        "group_index": 0,
        "group_sizes": [
          9
        ],
        "source_anchor": [
          3744,
          208
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              864,
              560
            ],
            "depot_type": 106,
            "owner": 0,
            "top_left_tile": [
              25,
              16
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              160,
              1904
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              3,
              58
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2176,
              2736
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              66,
              84
            ]
          }
        ],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            160,
            1904
          ],
          "depot_type": 106,
          "owner": null,
          "top_left_tile": [
            3,
            58
          ]
        },
        "mineral_indices": [
          177,
          172,
          174,
          175,
          176,
          173,
          171
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {},
        "parent_site_index": 4,
        "group_index": 0,
        "group_sizes": [
          7
        ],
        "source_anchor": [
          160,
          1904
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              864,
              560
            ],
            "depot_type": 106,
            "owner": 0,
            "top_left_tile": [
              25,
              16
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              160,
              1904
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              3,
              58
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2176,
              2736
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              66,
              84
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            2176,
            2736
          ],
          "depot_type": 106,
          "owner": null,
          "top_left_tile": [
            66,
            84
          ]
        },
        "mineral_indices": [
          201,
          202,
          197,
          204
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 2
        },
        "parent_site_index": 5,
        "group_index": 0,
        "group_sizes": [
          4
        ],
        "source_anchor": [
          2176,
          2736
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              864,
              560
            ],
            "depot_type": 106,
            "owner": 0,
            "top_left_tile": [
              25,
              16
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              160,
              1904
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              3,
              58
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2176,
              2736
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              66,
              84
            ]
          }
        ],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      }
    ]
  },
  "110": {
    "input_unit_sha256": "bc60d58d2e32d2ea29659ff9dbaeb68cf751dbaca5a66689fb5250e28385c37a",
    "moves": [
      {
        "index": 1,
        "before": [
          3744,
          1072,
          176,
          11
        ],
        "after": [
          3648,
          112,
          176,
          11
        ]
      },
      {
        "index": 2,
        "before": [
          3808,
          1072,
          178,
          11
        ],
        "after": [
          3648,
          144,
          178,
          11
        ]
      },
      {
        "index": 3,
        "before": [
          3520,
          48,
          176,
          11
        ],
        "after": [
          3360,
          48,
          176,
          11
        ]
      },
      {
        "index": 4,
        "before": [
          3648,
          144,
          177,
          11
        ],
        "after": [
          3488,
          48,
          177,
          11
        ]
      },
      {
        "index": 6,
        "before": [
          3392,
          48,
          176,
          11
        ],
        "after": [
          3232,
          112,
          176,
          11
        ]
      },
      {
        "index": 7,
        "before": [
          3584,
          1008,
          177,
          11
        ],
        "after": [
          3200,
          208,
          177,
          11
        ]
      },
      {
        "index": 10,
        "before": [
          3584,
          112,
          176,
          11
        ],
        "after": [
          3424,
          48,
          176,
          11
        ]
      },
      {
        "index": 11,
        "before": [
          3680,
          1072,
          177,
          11
        ],
        "after": [
          3616,
          80,
          177,
          11
        ]
      },
      {
        "index": 12,
        "before": [
          3616,
          1072,
          178,
          11
        ],
        "after": [
          3200,
          272,
          178,
          11
        ]
      },
      {
        "index": 13,
        "before": [
          3648,
          112,
          176,
          11
        ],
        "after": [
          3552,
          48,
          176,
          11
        ]
      },
      {
        "index": 15,
        "before": [
          3328,
          48,
          178,
          11
        ],
        "after": [
          3232,
          80,
          178,
          11
        ]
      },
      {
        "index": 16,
        "before": [
          3584,
          1040,
          176,
          11
        ],
        "after": [
          3200,
          240,
          176,
          11
        ]
      },
      {
        "index": 20,
        "before": [
          3584,
          976,
          177,
          11
        ],
        "after": [
          3232,
          176,
          177,
          11
        ]
      },
      {
        "index": 21,
        "before": [
          3456,
          48,
          178,
          11
        ],
        "after": [
          3296,
          48,
          178,
          11
        ]
      },
      {
        "index": 290,
        "before": [
          2880,
          3824,
          177,
          11
        ],
        "after": [
          3296,
          3792,
          177,
          11
        ]
      },
      {
        "index": 296,
        "before": [
          3520,
          3632,
          178,
          11
        ],
        "after": [
          3520,
          3568,
          178,
          11
        ]
      },
      {
        "index": 297,
        "before": [
          3520,
          3664,
          176,
          11
        ],
        "after": [
          3520,
          3600,
          176,
          11
        ]
      },
      {
        "index": 305,
        "before": [
          3296,
          3808,
          188,
          11
        ],
        "after": [
          3040,
          3648,
          188,
          11
        ]
      },
      {
        "index": 316,
        "before": [
          3520,
          3600,
          177,
          11
        ],
        "after": [
          3520,
          3536,
          177,
          11
        ]
      },
      {
        "index": 318,
        "before": [
          3520,
          3760,
          178,
          11
        ],
        "after": [
          3520,
          3696,
          178,
          11
        ]
      },
      {
        "index": 319,
        "before": [
          3104,
          3984,
          178,
          11
        ],
        "after": [
          3520,
          3760,
          178,
          11
        ]
      },
      {
        "index": 320,
        "before": [
          3520,
          3696,
          177,
          11
        ],
        "after": [
          3520,
          3632,
          177,
          11
        ]
      },
      {
        "index": 321,
        "before": [
          3456,
          3792,
          176,
          11
        ],
        "after": [
          3520,
          3728,
          176,
          11
        ]
      },
      {
        "index": 322,
        "before": [
          3040,
          3984,
          178,
          11
        ],
        "after": [
          3488,
          3792,
          178,
          11
        ]
      },
      {
        "index": 323,
        "before": [
          2976,
          4016,
          176,
          11
        ],
        "after": [
          3424,
          3792,
          176,
          11
        ]
      },
      {
        "index": 324,
        "before": [
          2880,
          3856,
          178,
          11
        ],
        "after": [
          3232,
          3792,
          178,
          11
        ]
      },
      {
        "index": 325,
        "before": [
          2912,
          4016,
          177,
          11
        ],
        "after": [
          3360,
          3792,
          177,
          11
        ]
      },
      {
        "index": 326,
        "before": [
          2848,
          3920,
          177,
          11
        ],
        "after": [
          3168,
          3792,
          177,
          11
        ]
      },
      {
        "index": 327,
        "before": [
          2928,
          3904,
          109,
          1
        ],
        "after": [
          3184,
          3520,
          109,
          1
        ]
      },
      {
        "index": 328,
        "before": [
          3520,
          3728,
          176,
          11
        ],
        "after": [
          3520,
          3664,
          176,
          11
        ]
      },
      {
        "index": 329,
        "before": [
          3024,
          3936,
          109,
          1
        ],
        "after": [
          3280,
          3520,
          109,
          1
        ]
      },
      {
        "index": 330,
        "before": [
          2928,
          3968,
          109,
          1
        ],
        "after": [
          3376,
          3520,
          109,
          1
        ]
      },
      {
        "index": 392,
        "before": [
          2848,
          3744,
          188,
          11
        ],
        "after": [
          3008,
          3776,
          188,
          11
        ]
      }
    ],
    "groups": [
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 60,
          "center": [
            3456,
            272
          ],
          "depot_type": 106,
          "owner": 6,
          "top_left_tile": [
            106,
            7
          ]
        },
        "mineral_indices": [
          6,
          13,
          4,
          15,
          21,
          3,
          10,
          2,
          1,
          11,
          12,
          20,
          7,
          16
        ],
        "gas_indices": [
          86
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 32
        },
        "parent_site_index": 0,
        "group_index": 0,
        "group_sizes": [
          14
        ],
        "source_anchor": [
          3456,
          272
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              3104,
              1488
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              95,
              45
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2080,
              1840
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              63,
              56
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "maximum_minerals": 14,
        "placement_policy": "reviewed_playtest_layout"
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 216,
          "center": [
            384,
            2512
          ],
          "depot_type": 106,
          "owner": 0,
          "top_left_tile": [
            10,
            77
          ]
        },
        "mineral_indices": [
          249,
          248,
          253,
          242,
          243,
          244,
          245,
          247,
          246,
          254,
          239
        ],
        "gas_indices": [
          218
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 1
        },
        "parent_site_index": 1,
        "group_index": 0,
        "group_sizes": [
          11
        ],
        "source_anchor": [
          384,
          2512
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              3104,
              1488
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              95,
              45
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2080,
              1840
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              63,
              56
            ]
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 300,
          "center": [
            3328,
            3632
          ],
          "depot_type": 106,
          "owner": 1,
          "top_left_tile": [
            102,
            112
          ]
        },
        "mineral_indices": [
          328,
          318,
          321,
          297,
          296,
          320,
          316,
          326,
          324,
          325,
          323,
          322,
          319,
          290
        ],
        "gas_indices": [
          305,
          392
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 10,
          "resource_overlap": 47,
          "gas_exit": 10,
          "geometry": 9,
          "depot_clearance": 14
        },
        "parent_site_index": 2,
        "group_index": 0,
        "group_sizes": [
          14
        ],
        "source_anchor": [
          3328,
          3632
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              3104,
              1488
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              95,
              45
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2080,
              1840
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              63,
              56
            ]
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "maximum_minerals": 14,
        "placement_policy": "reviewed_playtest_layout"
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            3104,
            1488
          ],
          "depot_type": 106,
          "owner": null,
          "top_left_tile": [
            95,
            45
          ]
        },
        "mineral_indices": [
          172,
          165,
          160,
          167,
          171,
          161,
          164
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 32
        },
        "parent_site_index": 3,
        "group_index": 0,
        "group_sizes": [
          7
        ],
        "source_anchor": [
          3104,
          1488
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              3104,
              1488
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              95,
              45
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2080,
              1840
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              63,
              56
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            2080,
            1840
          ],
          "depot_type": 106,
          "owner": null,
          "top_left_tile": [
            63,
            56
          ]
        },
        "mineral_indices": [
          158,
          178,
          180,
          163,
          175,
          179,
          159,
          169,
          174,
          168
        ],
        "gas_indices": [
          156
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 3
        },
        "parent_site_index": 4,
        "group_index": 0,
        "group_sizes": [
          10
        ],
        "source_anchor": [
          2080,
          1840
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              3104,
              1488
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              95,
              45
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2080,
              1840
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              63,
              56
            ]
          }
        ],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      }
    ],
    "wave_cell_changes": [
      {
        "index": 2,
        "before": {
          "mission_id": 110,
          "owner": 6,
          "race": 1,
          "unit1": 0,
          "unit2": 32,
          "cell_count": 8,
          "center": [
            3136,
            64
          ],
          "target": [
            3332,
            3636
          ],
          "cells": [
            [
              3220,
              52
            ],
            [
              3220,
              116
            ],
            [
              2996,
              84
            ],
            [
              3220,
              180
            ],
            [
              3188,
              212
            ],
            [
              3028,
              212
            ],
            [
              3252,
              212
            ],
            [
              3284,
              244
            ]
          ],
          "source_unit": 124,
          "ground_route_connected": true,
          "flying_only": false,
          "source_is_original_hostile_position": true,
          "friendly_clearance_pixels": 512,
          "original_occupancy_clearance_pixels": [
            40,
            80
          ]
        },
        "after": {
          "mission_id": 110,
          "owner": 6,
          "race": 1,
          "unit1": 0,
          "unit2": 32,
          "cell_count": 8,
          "center": [
            3136,
            64
          ],
          "target": [
            3332,
            3636
          ],
          "cells": [
            [
              3284,
              244
            ],
            [
              3348,
              212
            ],
            [
              3412,
              116
            ],
            [
              3412,
              180
            ],
            [
              3348,
              276
            ],
            [
              3444,
              148
            ],
            [
              3476,
              116
            ],
            [
              3476,
              180
            ]
          ],
          "source_unit": 124,
          "ground_route_connected": true,
          "flying_only": false,
          "source_is_original_hostile_position": true,
          "friendly_clearance_pixels": 512,
          "original_occupancy_clearance_pixels": [
            40,
            80
          ]
        }
      }
    ]
  },
  "202": {
    "input_unit_sha256": "25fa43468620283610f17975ece82415ea41a1dffb4acc288a0f8959d4c5e68a",
    "moves": [
      {
        "index": 119,
        "before": [
          480,
          2096,
          176,
          11
        ],
        "after": [
          768,
          2416,
          176,
          11
        ]
      },
      {
        "index": 122,
        "before": [
          480,
          2128,
          177,
          11
        ],
        "after": [
          704,
          2320,
          177,
          11
        ]
      },
      {
        "index": 123,
        "before": [
          672,
          2320,
          177,
          11
        ],
        "after": [
          832,
          2544,
          177,
          11
        ]
      },
      {
        "index": 125,
        "before": [
          416,
          2064,
          178,
          11
        ],
        "after": [
          544,
          2256,
          178,
          11
        ]
      },
      {
        "index": 126,
        "before": [
          608,
          2320,
          177,
          11
        ],
        "after": [
          832,
          2576,
          177,
          11
        ]
      },
      {
        "index": 127,
        "before": [
          544,
          2320,
          178,
          11
        ],
        "after": [
          768,
          2320,
          178,
          11
        ]
      },
      {
        "index": 128,
        "before": [
          480,
          2192,
          176,
          11
        ],
        "after": [
          480,
          2256,
          176,
          11
        ]
      },
      {
        "index": 129,
        "before": [
          480,
          2160,
          178,
          11
        ],
        "after": [
          608,
          2256,
          178,
          11
        ]
      },
      {
        "index": 130,
        "before": [
          480,
          2256,
          178,
          11
        ],
        "after": [
          416,
          2288,
          178,
          11
        ]
      },
      {
        "index": 131,
        "before": [
          416,
          2320,
          177,
          11
        ],
        "after": [
          800,
          2512,
          177,
          11
        ]
      },
      {
        "index": 133,
        "before": [
          480,
          2320,
          178,
          11
        ],
        "after": [
          768,
          2480,
          178,
          11
        ]
      },
      {
        "index": 134,
        "before": [
          480,
          2224,
          178,
          11
        ],
        "after": [
          768,
          2448,
          178,
          11
        ]
      },
      {
        "index": 135,
        "before": [
          736,
          2416,
          178,
          11
        ],
        "after": [
          896,
          2608,
          178,
          11
        ]
      },
      {
        "index": 136,
        "before": [
          736,
          2480,
          177,
          11
        ],
        "after": [
          896,
          2640,
          177,
          11
        ]
      },
      {
        "index": 140,
        "before": [
          480,
          2656,
          157,
          1
        ],
        "after": [
          480,
          2720,
          157,
          1
        ]
      },
      {
        "index": 145,
        "before": [
          864,
          624,
          131,
          3
        ],
        "after": [
          512,
          720,
          131,
          3
        ]
      }
    ],
    "groups": [
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 143,
          "center": [
            768,
            528
          ],
          "depot_type": 131,
          "owner": 3,
          "top_left_tile": [
            22,
            15
          ]
        },
        "mineral_indices": [
          31,
          32,
          33,
          37,
          21,
          29,
          35,
          42
        ],
        "gas_indices": [
          14
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "army_route": 12
        },
        "parent_site_index": 0,
        "group_index": 0,
        "group_sizes": [
          8,
          8
        ],
        "source_anchor": [
          768,
          528
        ],
        "planned_depot_sites": [],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "center": [
            512,
            720
          ],
          "depot_type": 131,
          "owner": 3,
          "top_left_tile": [
            14,
            21
          ],
          "additional_group_depot": true,
          "unit_index": 145,
          "occupied_by_relocated_depot": true
        },
        "mineral_indices": [
          30,
          43,
          47,
          27,
          23,
          46,
          28,
          48
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 1
        },
        "parent_site_index": 0,
        "group_index": 1,
        "group_sizes": [
          8,
          8
        ],
        "source_anchor": [
          768,
          528
        ],
        "planned_depot_sites": [],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 118,
          "center": [
            544,
            2480
          ],
          "depot_type": 154,
          "owner": 1,
          "top_left_tile": [
            15,
            76
          ]
        },
        "mineral_indices": [
          127,
          126,
          133,
          131,
          135,
          123,
          136,
          122,
          129,
          119,
          128,
          125,
          134,
          130
        ],
        "gas_indices": [
          140
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 32
        },
        "parent_site_index": 1,
        "group_index": 0,
        "group_sizes": [
          14
        ],
        "source_anchor": [
          544,
          2480
        ],
        "planned_depot_sites": [],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "maximum_minerals": 14,
        "placement_policy": "reviewed_playtest_layout"
      }
    ]
  },
  "207": {
    "input_unit_sha256": "272698c8b1a5e706f7fe3370ef56b752ba152e557327016d2319a81076254521",
    "moves": [
      {
        "index": 5,
        "before": [
          1504,
          720,
          177,
          11
        ],
        "after": [
          928,
          368,
          177,
          11
        ]
      },
      {
        "index": 7,
        "before": [
          1184,
          464,
          178,
          11
        ],
        "after": [
          800,
          400,
          178,
          11
        ]
      },
      {
        "index": 9,
        "before": [
          1120,
          336,
          178,
          11
        ],
        "after": [
          928,
          240,
          178,
          11
        ]
      },
      {
        "index": 10,
        "before": [
          1120,
          400,
          176,
          11
        ],
        "after": [
          1088,
          112,
          176,
          11
        ]
      },
      {
        "index": 11,
        "before": [
          1696,
          656,
          176,
          11
        ],
        "after": [
          1216,
          80,
          176,
          11
        ]
      },
      {
        "index": 18,
        "before": [
          1568,
          720,
          178,
          11
        ],
        "after": [
          1120,
          144,
          178,
          11
        ]
      },
      {
        "index": 20,
        "before": [
          1312,
          128,
          149,
          4
        ],
        "after": [
          1344,
          480,
          149,
          4
        ]
      },
      {
        "index": 21,
        "before": [
          1440,
          720,
          178,
          11
        ],
        "after": [
          928,
          336,
          178,
          11
        ]
      },
      {
        "index": 22,
        "before": [
          1120,
          368,
          178,
          11
        ],
        "after": [
          992,
          176,
          178,
          11
        ]
      },
      {
        "index": 23,
        "before": [
          1696,
          624,
          176,
          11
        ],
        "after": [
          1280,
          80,
          176,
          11
        ]
      },
      {
        "index": 27,
        "before": [
          1632,
          720,
          178,
          11
        ],
        "after": [
          1152,
          112,
          178,
          11
        ]
      },
      {
        "index": 28,
        "before": [
          1696,
          688,
          178,
          11
        ],
        "after": [
          1472,
          112,
          178,
          11
        ]
      },
      {
        "index": 29,
        "before": [
          1248,
          464,
          176,
          11
        ],
        "after": [
          1344,
          80,
          176,
          11
        ]
      },
      {
        "index": 35,
        "before": [
          1120,
          304,
          178,
          11
        ],
        "after": [
          928,
          208,
          178,
          11
        ]
      },
      {
        "index": 38,
        "before": [
          1312,
          464,
          178,
          11
        ],
        "after": [
          1408,
          80,
          178,
          11
        ]
      }
    ],
    "groups": [
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 184,
          "center": [
            1312,
            304
          ],
          "depot_type": 133,
          "owner": 4,
          "top_left_tile": [
            39,
            8
          ]
        },
        "mineral_indices": [
          29,
          35,
          38,
          22,
          9,
          10,
          7,
          21,
          5,
          18,
          28,
          23,
          11,
          27
        ],
        "gas_indices": [
          20
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 8,
          "depot_clearance": 24
        },
        "parent_site_index": 0,
        "group_index": 0,
        "group_sizes": [
          14
        ],
        "source_anchor": [
          1312,
          304
        ],
        "planned_depot_sites": [],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "maximum_minerals": 14,
        "placement_policy": "reviewed_playtest_layout"
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 182,
          "center": [
            2336,
            208
          ],
          "depot_type": 132,
          "owner": 4,
          "top_left_tile": [
            71,
            5
          ]
        },
        "mineral_indices": [
          13,
          4,
          17,
          24,
          26,
          39,
          30,
          46,
          0,
          3,
          19,
          12
        ],
        "gas_indices": [
          31
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "gas_inside_bank": 5
        },
        "parent_site_index": 1,
        "group_index": 0,
        "group_sizes": [
          12
        ],
        "source_anchor": [
          2336,
          208
        ],
        "planned_depot_sites": [],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 221,
          "center": [
            352,
            3056
          ],
          "depot_type": 131,
          "owner": 4,
          "top_left_tile": [
            9,
            94
          ]
        },
        "mineral_indices": [
          118,
          125,
          126,
          124,
          119,
          122,
          116,
          123,
          120,
          121,
          117,
          127
        ],
        "gas_indices": [
          130
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 3,
          "gas_inside_bank": 3,
          "gas_exit": 1
        },
        "parent_site_index": 2,
        "group_index": 0,
        "group_sizes": [
          12
        ],
        "source_anchor": [
          352,
          3056
        ],
        "planned_depot_sites": [],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 228,
          "center": [
            1824,
            3344
          ],
          "depot_type": 132,
          "owner": 4,
          "top_left_tile": [
            55,
            103
          ]
        },
        "mineral_indices": [
          135,
          136,
          141,
          142,
          132,
          134,
          138,
          144,
          146,
          139,
          140
        ],
        "gas_indices": [
          143,
          254
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 19,
          "resource_overlap": 11
        },
        "parent_site_index": 3,
        "group_index": 0,
        "group_sizes": [
          11
        ],
        "source_anchor": [
          1824,
          3344
        ],
        "planned_depot_sites": [],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 211,
          "center": [
            3712,
            1552
          ],
          "depot_type": 132,
          "owner": 4,
          "top_left_tile": [
            114,
            47
          ]
        },
        "mineral_indices": [
          79,
          80,
          81,
          96,
          94,
          97,
          91,
          99,
          84,
          82,
          101
        ],
        "gas_indices": [
          87
        ],
        "status": "ladder_separate_gas",
        "reasons": {},
        "parent_site_index": 4,
        "group_index": 0,
        "group_sizes": [
          11
        ],
        "source_anchor": [
          3712,
          1552
        ],
        "planned_depot_sites": [],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      }
    ]
  },
  "208": {
    "input_unit_sha256": "9c780d767cfaa326cac17eccd6cd38a94ddae317a08d1baf58f61680011688b3",
    "moves": [
      {
        "index": 150,
        "before": [
          704,
          3216,
          177,
          11
        ],
        "after": [
          608,
          3600,
          177,
          11
        ]
      },
      {
        "index": 157,
        "before": [
          672,
          2544,
          176,
          11
        ],
        "after": [
          640,
          3216,
          176,
          11
        ]
      },
      {
        "index": 159,
        "before": [
          608,
          2544,
          178,
          11
        ],
        "after": [
          576,
          3216,
          178,
          11
        ]
      },
      {
        "index": 161,
        "before": [
          768,
          3248,
          177,
          11
        ],
        "after": [
          768,
          3184,
          177,
          11
        ]
      },
      {
        "index": 168,
        "before": [
          544,
          2544,
          178,
          11
        ],
        "after": [
          576,
          3312,
          178,
          11
        ]
      },
      {
        "index": 171,
        "before": [
          480,
          2640,
          176,
          11
        ],
        "after": [
          544,
          3344,
          176,
          11
        ]
      },
      {
        "index": 172,
        "before": [
          640,
          3216,
          177,
          11
        ],
        "after": [
          608,
          3568,
          177,
          11
        ]
      },
      {
        "index": 174,
        "before": [
          480,
          2672,
          178,
          11
        ],
        "after": [
          544,
          3376,
          178,
          11
        ]
      },
      {
        "index": 175,
        "before": [
          608,
          3312,
          176,
          11
        ],
        "after": [
          544,
          3440,
          176,
          11
        ]
      },
      {
        "index": 179,
        "before": [
          480,
          2704,
          177,
          11
        ],
        "after": [
          544,
          3408,
          177,
          11
        ]
      },
      {
        "index": 180,
        "before": [
          608,
          3408,
          178,
          11
        ],
        "after": [
          576,
          3536,
          178,
          11
        ]
      },
      {
        "index": 181,
        "before": [
          608,
          3440,
          177,
          11
        ],
        "after": [
          576,
          3504,
          177,
          11
        ]
      },
      {
        "index": 182,
        "before": [
          736,
          2544,
          177,
          11
        ],
        "after": [
          704,
          3184,
          177,
          11
        ]
      },
      {
        "index": 184,
        "before": [
          576,
          3680,
          188,
          11
        ],
        "after": [
          1024,
          3296,
          188,
          11
        ]
      },
      {
        "index": 186,
        "before": [
          608,
          3472,
          178,
          11
        ],
        "after": [
          544,
          3472,
          178,
          11
        ]
      },
      {
        "index": 197,
        "before": [
          3808,
          3776,
          134,
          3
        ],
        "after": [
          3552,
          3744,
          134,
          3
        ]
      }
    ],
    "groups": [
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 158,
          "center": [
            800,
            3408
          ],
          "depot_type": 154,
          "owner": 1,
          "top_left_tile": [
            23,
            105
          ]
        },
        "mineral_indices": [
          161,
          150,
          172,
          180,
          175,
          181,
          186,
          157,
          159,
          168,
          171,
          174,
          179,
          182
        ],
        "gas_indices": [
          184
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 32,
          "gas_exit": 3,
          "gas_lane": 1
        },
        "parent_site_index": 0,
        "group_index": 0,
        "group_sizes": [
          14
        ],
        "source_anchor": [
          800,
          3408
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              1824,
              144
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              55,
              3
            ]
          },
          {
            "kind": "expansion",
            "center": [
              96,
              1296
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              1,
              39
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "maximum_minerals": 14,
        "placement_policy": "reviewed_playtest_layout"
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 93,
          "center": [
            3424,
            2416
          ],
          "depot_type": 154,
          "owner": 2,
          "top_left_tile": [
            105,
            74
          ]
        },
        "mineral_indices": [
          103,
          100,
          110,
          105,
          104,
          112,
          107,
          106,
          109
        ],
        "gas_indices": [
          91,
          120
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 12,
          "resource_overlap": 9
        },
        "parent_site_index": 1,
        "group_index": 0,
        "group_sizes": [
          9
        ],
        "source_anchor": [
          3424,
          2416
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              1824,
              144
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              55,
              3
            ]
          },
          {
            "kind": "expansion",
            "center": [
              96,
              1296
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              1,
              39
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 196,
          "center": [
            3648,
            3664
          ],
          "depot_type": 131,
          "owner": 3,
          "top_left_tile": [
            112,
            113
          ]
        },
        "mineral_indices": [
          148,
          133,
          144,
          140,
          147,
          136,
          139,
          143
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 33,
          "geometry": 3,
          "army_route": 3
        },
        "parent_site_index": 2,
        "group_index": 0,
        "group_sizes": [
          8
        ],
        "source_anchor": [
          3648,
          3664
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              1824,
              144
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              55,
              3
            ]
          },
          {
            "kind": "expansion",
            "center": [
              96,
              1296
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              1,
              39
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            1824,
            144
          ],
          "depot_type": 131,
          "owner": null,
          "top_left_tile": [
            55,
            3
          ]
        },
        "mineral_indices": [
          5,
          1,
          8,
          0,
          4,
          12
        ],
        "gas_indices": [
          18
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 24,
          "geometry": 3
        },
        "parent_site_index": 3,
        "group_index": 0,
        "group_sizes": [
          6
        ],
        "source_anchor": [
          1824,
          144
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              1824,
              144
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              55,
              3
            ]
          },
          {
            "kind": "expansion",
            "center": [
              96,
              1296
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              1,
              39
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            96,
            1296
          ],
          "depot_type": 131,
          "owner": null,
          "top_left_tile": [
            1,
            39
          ]
        },
        "mineral_indices": [
          63,
          65,
          67,
          58,
          62,
          66
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 198,
          "army_route": 3
        },
        "parent_site_index": 4,
        "group_index": 0,
        "group_sizes": [
          6
        ],
        "source_anchor": [
          96,
          1296
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              1824,
              144
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              55,
              3
            ]
          },
          {
            "kind": "expansion",
            "center": [
              96,
              1296
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              1,
              39
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 191,
          "center": [
            3424,
            336
          ],
          "depot_type": 131,
          "owner": 3,
          "top_left_tile": [
            105,
            9
          ]
        },
        "mineral_indices": [
          7,
          11,
          23,
          20,
          25,
          15,
          26,
          28
        ],
        "gas_indices": [
          30,
          212
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "resource_overlap": 2
        },
        "parent_site_index": 5,
        "group_index": 0,
        "group_sizes": [
          8
        ],
        "source_anchor": [
          3424,
          336
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              1824,
              144
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              55,
              3
            ]
          },
          {
            "kind": "expansion",
            "center": [
              96,
              1296
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              1,
              39
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      }
    ]
  },
  "210": {
    "input_unit_sha256": "08bcf562b4dfb335a3c455fc58e2eb6fe547dadce5d795fd7e33170f2b9e8742",
    "moves": [
      {
        "index": 369,
        "before": [
          3456,
          7472,
          178,
          11
        ],
        "after": [
          3488,
          7760,
          178,
          11
        ]
      },
      {
        "index": 373,
        "before": [
          3456,
          7504,
          177,
          11
        ],
        "after": [
          3456,
          7824,
          177,
          11
        ]
      },
      {
        "index": 399,
        "before": [
          3456,
          7536,
          177,
          11
        ],
        "after": [
          3456,
          7856,
          177,
          11
        ]
      },
      {
        "index": 401,
        "before": [
          3584,
          7440,
          178,
          11
        ],
        "after": [
          3616,
          7760,
          178,
          11
        ]
      },
      {
        "index": 406,
        "before": [
          3840,
          7856,
          177,
          11
        ],
        "after": [
          3808,
          7760,
          177,
          11
        ]
      },
      {
        "index": 407,
        "before": [
          3840,
          7920,
          177,
          11
        ],
        "after": [
          3456,
          8016,
          177,
          11
        ]
      },
      {
        "index": 412,
        "before": [
          3776,
          7760,
          178,
          11
        ],
        "after": [
          3744,
          7760,
          178,
          11
        ]
      },
      {
        "index": 413,
        "before": [
          3648,
          7760,
          178,
          11
        ],
        "after": [
          3456,
          7984,
          178,
          11
        ]
      },
      {
        "index": 419,
        "before": [
          3520,
          7440,
          178,
          11
        ],
        "after": [
          3552,
          7760,
          178,
          11
        ]
      },
      {
        "index": 420,
        "before": [
          3584,
          7760,
          178,
          11
        ],
        "after": [
          3456,
          7952,
          178,
          11
        ]
      },
      {
        "index": 428,
        "before": [
          3712,
          7760,
          177,
          11
        ],
        "after": [
          3680,
          7760,
          177,
          11
        ]
      },
      {
        "index": 433,
        "before": [
          3456,
          7568,
          178,
          11
        ],
        "after": [
          3456,
          7888,
          178,
          11
        ]
      },
      {
        "index": 440,
        "before": [
          3456,
          7600,
          176,
          11
        ],
        "after": [
          3456,
          7920,
          176,
          11
        ]
      }
    ],
    "groups": [
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 16,
          "center": [
            2752,
            176
          ],
          "depot_type": 154,
          "owner": 0,
          "top_left_tile": [
            84,
            4
          ]
        },
        "mineral_indices": [
          45,
          51,
          53,
          60,
          66,
          47,
          64,
          80,
          65,
          54,
          55
        ],
        "gas_indices": [
          11,
          15
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 11,
          "resource_overlap": 439,
          "depot_clearance": 144
        },
        "parent_site_index": 0,
        "group_index": 0,
        "group_sizes": [
          11,
          11,
          11
        ],
        "source_anchor": [
          2752,
          176
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              2944,
              432
            ],
            "depot_type": 154,
            "owner": 0,
            "top_left_tile": [
              90,
              12
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              2368,
              176
            ],
            "depot_type": 154,
            "owner": 0,
            "top_left_tile": [
              72,
              4
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1792,
              1552
            ],
            "depot_type": 154,
            "owner": 7,
            "top_left_tile": [
              54,
              47
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              2304,
              8080
            ],
            "depot_type": 131,
            "owner": 3,
            "top_left_tile": [
              70,
              251
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1152,
              7696
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              34,
              239
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3872,
              3920
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              119,
              121
            ]
          },
          {
            "kind": "expansion",
            "center": [
              128,
              4400
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              2,
              136
            ]
          },
          {
            "kind": "expansion",
            "center": [
              608,
              6288
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              17,
              195
            ]
          },
          {
            "kind": "expansion",
            "center": [
              64,
              5520
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              0,
              171
            ]
          }
        ],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            2944,
            432
          ],
          "depot_type": 154,
          "owner": 0,
          "top_left_tile": [
            90,
            12
          ],
          "additional_group_depot": true
        },
        "mineral_indices": [
          57,
          43,
          63,
          74,
          46,
          76,
          72,
          71,
          81,
          84,
          77
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 29,
          "plateau": 27
        },
        "parent_site_index": 0,
        "group_index": 1,
        "group_sizes": [
          11,
          11,
          11
        ],
        "source_anchor": [
          2752,
          176
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              2944,
              432
            ],
            "depot_type": 154,
            "owner": 0,
            "top_left_tile": [
              90,
              12
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              2368,
              176
            ],
            "depot_type": 154,
            "owner": 0,
            "top_left_tile": [
              72,
              4
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1792,
              1552
            ],
            "depot_type": 154,
            "owner": 7,
            "top_left_tile": [
              54,
              47
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              2304,
              8080
            ],
            "depot_type": 131,
            "owner": 3,
            "top_left_tile": [
              70,
              251
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1152,
              7696
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              34,
              239
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3872,
              3920
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              119,
              121
            ]
          },
          {
            "kind": "expansion",
            "center": [
              128,
              4400
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              2,
              136
            ]
          },
          {
            "kind": "expansion",
            "center": [
              608,
              6288
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              17,
              195
            ]
          },
          {
            "kind": "expansion",
            "center": [
              64,
              5520
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              0,
              171
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            2368,
            176
          ],
          "depot_type": 154,
          "owner": 0,
          "top_left_tile": [
            72,
            4
          ],
          "additional_group_depot": true
        },
        "mineral_indices": [
          52,
          61,
          75,
          56,
          62,
          44,
          70,
          82,
          48,
          78,
          73
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 2
        },
        "parent_site_index": 0,
        "group_index": 2,
        "group_sizes": [
          11,
          11,
          11
        ],
        "source_anchor": [
          2752,
          176
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              2944,
              432
            ],
            "depot_type": 154,
            "owner": 0,
            "top_left_tile": [
              90,
              12
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              2368,
              176
            ],
            "depot_type": 154,
            "owner": 0,
            "top_left_tile": [
              72,
              4
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1792,
              1552
            ],
            "depot_type": 154,
            "owner": 7,
            "top_left_tile": [
              54,
              47
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              2304,
              8080
            ],
            "depot_type": 131,
            "owner": 3,
            "top_left_tile": [
              70,
              251
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1152,
              7696
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              34,
              239
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3872,
              3920
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              119,
              121
            ]
          },
          {
            "kind": "expansion",
            "center": [
              128,
              4400
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              2,
              136
            ]
          },
          {
            "kind": "expansion",
            "center": [
              608,
              6288
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              17,
              195
            ]
          },
          {
            "kind": "expansion",
            "center": [
              64,
              5520
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              0,
              171
            ]
          }
        ],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 135,
          "center": [
            1984,
            1296
          ],
          "depot_type": 154,
          "owner": 7,
          "top_left_tile": [
            60,
            39
          ]
        },
        "mineral_indices": [
          129,
          144,
          122,
          123,
          124,
          130,
          132,
          147
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 1,
          "geometry": 1,
          "depot_clearance": 1
        },
        "parent_site_index": 1,
        "group_index": 0,
        "group_sizes": [
          8,
          8
        ],
        "source_anchor": [
          1984,
          1296
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              2944,
              432
            ],
            "depot_type": 154,
            "owner": 0,
            "top_left_tile": [
              90,
              12
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              2368,
              176
            ],
            "depot_type": 154,
            "owner": 0,
            "top_left_tile": [
              72,
              4
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1792,
              1552
            ],
            "depot_type": 154,
            "owner": 7,
            "top_left_tile": [
              54,
              47
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              2304,
              8080
            ],
            "depot_type": 131,
            "owner": 3,
            "top_left_tile": [
              70,
              251
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1152,
              7696
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              34,
              239
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3872,
              3920
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              119,
              121
            ]
          },
          {
            "kind": "expansion",
            "center": [
              128,
              4400
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              2,
              136
            ]
          },
          {
            "kind": "expansion",
            "center": [
              608,
              6288
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              17,
              195
            ]
          },
          {
            "kind": "expansion",
            "center": [
              64,
              5520
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              0,
              171
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            1792,
            1552
          ],
          "depot_type": 154,
          "owner": 7,
          "top_left_tile": [
            54,
            47
          ],
          "additional_group_depot": true
        },
        "mineral_indices": [
          139,
          150,
          143,
          138,
          115,
          117,
          119,
          118
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 8,
          "plateau": 3
        },
        "parent_site_index": 1,
        "group_index": 1,
        "group_sizes": [
          8,
          8
        ],
        "source_anchor": [
          1984,
          1296
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              2944,
              432
            ],
            "depot_type": 154,
            "owner": 0,
            "top_left_tile": [
              90,
              12
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              2368,
              176
            ],
            "depot_type": 154,
            "owner": 0,
            "top_left_tile": [
              72,
              4
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1792,
              1552
            ],
            "depot_type": 154,
            "owner": 7,
            "top_left_tile": [
              54,
              47
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              2304,
              8080
            ],
            "depot_type": 131,
            "owner": 3,
            "top_left_tile": [
              70,
              251
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1152,
              7696
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              34,
              239
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3872,
              3920
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              119,
              121
            ]
          },
          {
            "kind": "expansion",
            "center": [
              128,
              4400
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              2,
              136
            ]
          },
          {
            "kind": "expansion",
            "center": [
              608,
              6288
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              17,
              195
            ]
          },
          {
            "kind": "expansion",
            "center": [
              64,
              5520
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              0,
              171
            ]
          }
        ],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 444,
          "center": [
            2048,
            7888
          ],
          "depot_type": 131,
          "owner": 3,
          "top_left_tile": [
            62,
            245
          ]
        },
        "mineral_indices": [
          434,
          442,
          436,
          425,
          437,
          418,
          411,
          427
        ],
        "gas_indices": [
          359,
          488
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 11,
          "resource_overlap": 25,
          "gas_exit": 1,
          "gas_lane": 2
        },
        "parent_site_index": 2,
        "group_index": 0,
        "group_sizes": [
          8,
          8
        ],
        "source_anchor": [
          2048,
          7888
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              2944,
              432
            ],
            "depot_type": 154,
            "owner": 0,
            "top_left_tile": [
              90,
              12
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              2368,
              176
            ],
            "depot_type": 154,
            "owner": 0,
            "top_left_tile": [
              72,
              4
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1792,
              1552
            ],
            "depot_type": 154,
            "owner": 7,
            "top_left_tile": [
              54,
              47
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              2304,
              8080
            ],
            "depot_type": 131,
            "owner": 3,
            "top_left_tile": [
              70,
              251
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1152,
              7696
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              34,
              239
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3872,
              3920
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              119,
              121
            ]
          },
          {
            "kind": "expansion",
            "center": [
              128,
              4400
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              2,
              136
            ]
          },
          {
            "kind": "expansion",
            "center": [
              608,
              6288
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              17,
              195
            ]
          },
          {
            "kind": "expansion",
            "center": [
              64,
              5520
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              0,
              171
            ]
          }
        ],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            2304,
            8080
          ],
          "depot_type": 131,
          "owner": 3,
          "top_left_tile": [
            70,
            251
          ],
          "additional_group_depot": true
        },
        "mineral_indices": [
          438,
          429,
          392,
          376,
          383,
          441,
          435,
          443
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 4,
          "plateau": 4
        },
        "parent_site_index": 2,
        "group_index": 1,
        "group_sizes": [
          8,
          8
        ],
        "source_anchor": [
          2048,
          7888
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              2944,
              432
            ],
            "depot_type": 154,
            "owner": 0,
            "top_left_tile": [
              90,
              12
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              2368,
              176
            ],
            "depot_type": 154,
            "owner": 0,
            "top_left_tile": [
              72,
              4
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1792,
              1552
            ],
            "depot_type": 154,
            "owner": 7,
            "top_left_tile": [
              54,
              47
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              2304,
              8080
            ],
            "depot_type": 131,
            "owner": 3,
            "top_left_tile": [
              70,
              251
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1152,
              7696
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              34,
              239
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3872,
              3920
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              119,
              121
            ]
          },
          {
            "kind": "expansion",
            "center": [
              128,
              4400
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              2,
              136
            ]
          },
          {
            "kind": "expansion",
            "center": [
              608,
              6288
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              17,
              195
            ]
          },
          {
            "kind": "expansion",
            "center": [
              64,
              5520
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              0,
              171
            ]
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            1152,
            7696
          ],
          "depot_type": 131,
          "owner": null,
          "top_left_tile": [
            34,
            239
          ]
        },
        "mineral_indices": [
          382,
          390,
          400,
          414,
          409,
          430,
          391,
          421,
          404
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 2
        },
        "parent_site_index": 3,
        "group_index": 0,
        "group_sizes": [
          9
        ],
        "source_anchor": [
          1152,
          7696
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              2944,
              432
            ],
            "depot_type": 154,
            "owner": 0,
            "top_left_tile": [
              90,
              12
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              2368,
              176
            ],
            "depot_type": 154,
            "owner": 0,
            "top_left_tile": [
              72,
              4
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1792,
              1552
            ],
            "depot_type": 154,
            "owner": 7,
            "top_left_tile": [
              54,
              47
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              2304,
              8080
            ],
            "depot_type": 131,
            "owner": 3,
            "top_left_tile": [
              70,
              251
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1152,
              7696
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              34,
              239
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3872,
              3920
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              119,
              121
            ]
          },
          {
            "kind": "expansion",
            "center": [
              128,
              4400
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              2,
              136
            ]
          },
          {
            "kind": "expansion",
            "center": [
              608,
              6288
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              17,
              195
            ]
          },
          {
            "kind": "expansion",
            "center": [
              64,
              5520
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              0,
              171
            ]
          }
        ],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 365,
          "center": [
            256,
            7728
          ],
          "depot_type": 154,
          "owner": 2,
          "top_left_tile": [
            6,
            240
          ]
        },
        "mineral_indices": [
          405,
          415,
          426,
          432,
          431,
          439,
          422,
          423,
          416
        ],
        "gas_indices": [
          358
        ],
        "status": "ladder_separate_gas",
        "reasons": {},
        "parent_site_index": 4,
        "group_index": 0,
        "group_sizes": [
          9
        ],
        "source_anchor": [
          256,
          7728
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              2944,
              432
            ],
            "depot_type": 154,
            "owner": 0,
            "top_left_tile": [
              90,
              12
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              2368,
              176
            ],
            "depot_type": 154,
            "owner": 0,
            "top_left_tile": [
              72,
              4
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1792,
              1552
            ],
            "depot_type": 154,
            "owner": 7,
            "top_left_tile": [
              54,
              47
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              2304,
              8080
            ],
            "depot_type": 131,
            "owner": 3,
            "top_left_tile": [
              70,
              251
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1152,
              7696
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              34,
              239
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3872,
              3920
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              119,
              121
            ]
          },
          {
            "kind": "expansion",
            "center": [
              128,
              4400
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              2,
              136
            ]
          },
          {
            "kind": "expansion",
            "center": [
              608,
              6288
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              17,
              195
            ]
          },
          {
            "kind": "expansion",
            "center": [
              64,
              5520
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              0,
              171
            ]
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 408,
          "center": [
            3648,
            7920
          ],
          "depot_type": 154,
          "owner": 2,
          "top_left_tile": [
            112,
            246
          ]
        },
        "mineral_indices": [
          407,
          406,
          412,
          420,
          413,
          428,
          401,
          419,
          369,
          373,
          399,
          433,
          440
        ],
        "gas_indices": [
          366
        ],
        "status": "ladder_separate_gas",
        "reasons": {},
        "parent_site_index": 5,
        "group_index": 0,
        "group_sizes": [
          13
        ],
        "source_anchor": [
          3648,
          7920
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              2944,
              432
            ],
            "depot_type": 154,
            "owner": 0,
            "top_left_tile": [
              90,
              12
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              2368,
              176
            ],
            "depot_type": 154,
            "owner": 0,
            "top_left_tile": [
              72,
              4
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1792,
              1552
            ],
            "depot_type": 154,
            "owner": 7,
            "top_left_tile": [
              54,
              47
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              2304,
              8080
            ],
            "depot_type": 131,
            "owner": 3,
            "top_left_tile": [
              70,
              251
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1152,
              7696
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              34,
              239
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3872,
              3920
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              119,
              121
            ]
          },
          {
            "kind": "expansion",
            "center": [
              128,
              4400
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              2,
              136
            ]
          },
          {
            "kind": "expansion",
            "center": [
              608,
              6288
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              17,
              195
            ]
          },
          {
            "kind": "expansion",
            "center": [
              64,
              5520
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              0,
              171
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "maximum_minerals": 13,
        "placement_policy": "reviewed_playtest_layout"
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            3872,
            3920
          ],
          "depot_type": 131,
          "owner": null,
          "top_left_tile": [
            119,
            121
          ]
        },
        "mineral_indices": [
          281,
          276,
          277,
          275,
          278,
          282
        ],
        "gas_indices": [
          292
        ],
        "status": "ladder_separate_gas",
        "reasons": {},
        "parent_site_index": 6,
        "group_index": 0,
        "group_sizes": [
          6
        ],
        "source_anchor": [
          3872,
          3920
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              2944,
              432
            ],
            "depot_type": 154,
            "owner": 0,
            "top_left_tile": [
              90,
              12
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              2368,
              176
            ],
            "depot_type": 154,
            "owner": 0,
            "top_left_tile": [
              72,
              4
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1792,
              1552
            ],
            "depot_type": 154,
            "owner": 7,
            "top_left_tile": [
              54,
              47
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              2304,
              8080
            ],
            "depot_type": 131,
            "owner": 3,
            "top_left_tile": [
              70,
              251
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1152,
              7696
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              34,
              239
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3872,
              3920
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              119,
              121
            ]
          },
          {
            "kind": "expansion",
            "center": [
              128,
              4400
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              2,
              136
            ]
          },
          {
            "kind": "expansion",
            "center": [
              608,
              6288
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              17,
              195
            ]
          },
          {
            "kind": "expansion",
            "center": [
              64,
              5520
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              0,
              171
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            128,
            4400
          ],
          "depot_type": 131,
          "owner": null,
          "top_left_tile": [
            2,
            136
          ]
        },
        "mineral_indices": [
          283,
          290,
          291,
          289,
          286,
          287
        ],
        "gas_indices": [
          294
        ],
        "status": "ladder_separate_gas",
        "reasons": {},
        "parent_site_index": 7,
        "group_index": 0,
        "group_sizes": [
          6
        ],
        "source_anchor": [
          128,
          4400
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              2944,
              432
            ],
            "depot_type": 154,
            "owner": 0,
            "top_left_tile": [
              90,
              12
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              2368,
              176
            ],
            "depot_type": 154,
            "owner": 0,
            "top_left_tile": [
              72,
              4
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1792,
              1552
            ],
            "depot_type": 154,
            "owner": 7,
            "top_left_tile": [
              54,
              47
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              2304,
              8080
            ],
            "depot_type": 131,
            "owner": 3,
            "top_left_tile": [
              70,
              251
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1152,
              7696
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              34,
              239
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3872,
              3920
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              119,
              121
            ]
          },
          {
            "kind": "expansion",
            "center": [
              128,
              4400
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              2,
              136
            ]
          },
          {
            "kind": "expansion",
            "center": [
              608,
              6288
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              17,
              195
            ]
          },
          {
            "kind": "expansion",
            "center": [
              64,
              5520
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              0,
              171
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            608,
            6288
          ],
          "depot_type": 131,
          "owner": null,
          "top_left_tile": [
            17,
            195
          ]
        },
        "mineral_indices": [
          314,
          308,
          309,
          313,
          312,
          310
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {},
        "parent_site_index": 8,
        "group_index": 0,
        "group_sizes": [
          6
        ],
        "source_anchor": [
          608,
          6288
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              2944,
              432
            ],
            "depot_type": 154,
            "owner": 0,
            "top_left_tile": [
              90,
              12
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              2368,
              176
            ],
            "depot_type": 154,
            "owner": 0,
            "top_left_tile": [
              72,
              4
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1792,
              1552
            ],
            "depot_type": 154,
            "owner": 7,
            "top_left_tile": [
              54,
              47
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              2304,
              8080
            ],
            "depot_type": 131,
            "owner": 3,
            "top_left_tile": [
              70,
              251
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1152,
              7696
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              34,
              239
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3872,
              3920
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              119,
              121
            ]
          },
          {
            "kind": "expansion",
            "center": [
              128,
              4400
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              2,
              136
            ]
          },
          {
            "kind": "expansion",
            "center": [
              608,
              6288
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              17,
              195
            ]
          },
          {
            "kind": "expansion",
            "center": [
              64,
              5520
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              0,
              171
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            64,
            5520
          ],
          "depot_type": 131,
          "owner": null,
          "top_left_tile": [
            0,
            171
          ]
        },
        "mineral_indices": [
          304,
          305,
          300,
          295,
          297,
          306
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 5
        },
        "parent_site_index": 9,
        "group_index": 0,
        "group_sizes": [
          6
        ],
        "source_anchor": [
          64,
          5520
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              2944,
              432
            ],
            "depot_type": 154,
            "owner": 0,
            "top_left_tile": [
              90,
              12
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              2368,
              176
            ],
            "depot_type": 154,
            "owner": 0,
            "top_left_tile": [
              72,
              4
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1792,
              1552
            ],
            "depot_type": 154,
            "owner": 7,
            "top_left_tile": [
              54,
              47
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              2304,
              8080
            ],
            "depot_type": 131,
            "owner": 3,
            "top_left_tile": [
              70,
              251
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1152,
              7696
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              34,
              239
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3872,
              3920
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              119,
              121
            ]
          },
          {
            "kind": "expansion",
            "center": [
              128,
              4400
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              2,
              136
            ]
          },
          {
            "kind": "expansion",
            "center": [
              608,
              6288
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              17,
              195
            ]
          },
          {
            "kind": "expansion",
            "center": [
              64,
              5520
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              0,
              171
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      }
    ]
  },
  "303": {
    "input_unit_sha256": "7be994e62abcc10bad15ab8d4101f141052035cdfbeb5d33780cb5c022af91c4",
    "moves": [
      {
        "index": 135,
        "before": [
          3456,
          2832,
          176,
          11
        ],
        "after": [
          3712,
          2736,
          176,
          11
        ]
      },
      {
        "index": 140,
        "before": [
          3712,
          2704,
          176,
          11
        ],
        "after": [
          3712,
          2576,
          176,
          11
        ]
      },
      {
        "index": 145,
        "before": [
          3456,
          2864,
          178,
          11
        ],
        "after": [
          3616,
          2800,
          178,
          11
        ]
      },
      {
        "index": 150,
        "before": [
          3456,
          2896,
          177,
          11
        ],
        "after": [
          3680,
          2800,
          177,
          11
        ]
      },
      {
        "index": 151,
        "before": [
          3648,
          2800,
          177,
          11
        ],
        "after": [
          3712,
          2608,
          177,
          11
        ]
      },
      {
        "index": 152,
        "before": [
          3200,
          2992,
          178,
          11
        ],
        "after": [
          3360,
          2800,
          178,
          11
        ]
      },
      {
        "index": 154,
        "before": [
          3392,
          2992,
          178,
          11
        ],
        "after": [
          3552,
          2800,
          178,
          11
        ]
      },
      {
        "index": 155,
        "before": [
          3520,
          2800,
          176,
          11
        ],
        "after": [
          3712,
          2672,
          176,
          11
        ]
      },
      {
        "index": 157,
        "before": [
          3328,
          2992,
          178,
          11
        ],
        "after": [
          3488,
          2800,
          178,
          11
        ]
      },
      {
        "index": 158,
        "before": [
          3712,
          2640,
          177,
          11
        ],
        "after": [
          3712,
          2544,
          177,
          11
        ]
      },
      {
        "index": 159,
        "before": [
          3456,
          2800,
          178,
          11
        ],
        "after": [
          3712,
          2640,
          178,
          11
        ]
      },
      {
        "index": 161,
        "before": [
          3264,
          2992,
          178,
          11
        ],
        "after": [
          3424,
          2800,
          178,
          11
        ]
      },
      {
        "index": 162,
        "before": [
          3584,
          2800,
          178,
          11
        ],
        "after": [
          3712,
          2704,
          178,
          11
        ]
      }
    ],
    "groups": [
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 125,
          "center": [
            3520,
            2640
          ],
          "depot_type": 154,
          "owner": 7,
          "top_left_tile": [
            108,
            81
          ]
        },
        "mineral_indices": [
          155,
          159,
          162,
          140,
          151,
          158,
          152,
          161,
          154,
          157,
          150,
          145,
          135
        ],
        "gas_indices": [
          121
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 1
        },
        "parent_site_index": 0,
        "group_index": 0,
        "group_sizes": [
          13
        ],
        "source_anchor": [
          3520,
          2640
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              256,
              336
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              6,
              9
            ]
          },
          {
            "kind": "expansion",
            "center": [
              1472,
              336
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              44,
              9
            ]
          },
          {
            "kind": "expansion",
            "center": [
              480,
              2864
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              13,
              88
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "maximum_minerals": 13,
        "placement_policy": "reviewed_playtest_layout"
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            256,
            336
          ],
          "depot_type": 154,
          "owner": null,
          "top_left_tile": [
            6,
            9
          ]
        },
        "mineral_indices": [
          2,
          1,
          7,
          13,
          12,
          15,
          8,
          18,
          6
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {},
        "parent_site_index": 1,
        "group_index": 0,
        "group_sizes": [
          9
        ],
        "source_anchor": [
          256,
          336
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              256,
              336
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              6,
              9
            ]
          },
          {
            "kind": "expansion",
            "center": [
              1472,
              336
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              44,
              9
            ]
          },
          {
            "kind": "expansion",
            "center": [
              480,
              2864
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              13,
              88
            ]
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            1472,
            336
          ],
          "depot_type": 154,
          "owner": null,
          "top_left_tile": [
            44,
            9
          ]
        },
        "mineral_indices": [
          11,
          10,
          14,
          4,
          3,
          5,
          0,
          9
        ],
        "gas_indices": [
          20
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 1
        },
        "parent_site_index": 2,
        "group_index": 0,
        "group_sizes": [
          8
        ],
        "source_anchor": [
          1472,
          336
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              256,
              336
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              6,
              9
            ]
          },
          {
            "kind": "expansion",
            "center": [
              1472,
              336
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              44,
              9
            ]
          },
          {
            "kind": "expansion",
            "center": [
              480,
              2864
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              13,
              88
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 188,
          "center": [
            960,
            1776
          ],
          "depot_type": 133,
          "owner": 0,
          "top_left_tile": [
            28,
            54
          ]
        },
        "mineral_indices": [
          111,
          113,
          109,
          114,
          112,
          105,
          110,
          115
        ],
        "gas_indices": [
          68,
          116
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 4,
          "resource_overlap": 39,
          "gas_lane": 62,
          "gas_exit": 48
        },
        "parent_site_index": 3,
        "group_index": 0,
        "group_sizes": [
          8
        ],
        "source_anchor": [
          960,
          1776
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              256,
              336
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              6,
              9
            ]
          },
          {
            "kind": "expansion",
            "center": [
              1472,
              336
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              44,
              9
            ]
          },
          {
            "kind": "expansion",
            "center": [
              480,
              2864
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              13,
              88
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 169,
          "center": [
            3712,
            624
          ],
          "depot_type": 132,
          "owner": 6,
          "top_left_tile": [
            114,
            18
          ]
        },
        "mineral_indices": [
          21,
          24,
          27,
          25,
          23,
          26,
          22
        ],
        "gas_indices": [
          50
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 32
        },
        "parent_site_index": 4,
        "group_index": 0,
        "group_sizes": [
          7
        ],
        "source_anchor": [
          3712,
          624
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              256,
              336
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              6,
              9
            ]
          },
          {
            "kind": "expansion",
            "center": [
              1472,
              336
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              44,
              9
            ]
          },
          {
            "kind": "expansion",
            "center": [
              480,
              2864
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              13,
              88
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            480,
            2864
          ],
          "depot_type": 154,
          "owner": null,
          "top_left_tile": [
            13,
            88
          ]
        },
        "mineral_indices": [
          146,
          147,
          153,
          163,
          160,
          164,
          156
        ],
        "gas_indices": [
          126
        ],
        "status": "ladder_separate_gas",
        "reasons": {},
        "parent_site_index": 5,
        "group_index": 0,
        "group_sizes": [
          7
        ],
        "source_anchor": [
          480,
          2864
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              256,
              336
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              6,
              9
            ]
          },
          {
            "kind": "expansion",
            "center": [
              1472,
              336
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              44,
              9
            ]
          },
          {
            "kind": "expansion",
            "center": [
              480,
              2864
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              13,
              88
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      }
    ]
  },
  "304": {
    "input_unit_sha256": "e20564c48f91a8092677fef48ce22344076af6f7fd4b7b823d8a20909a3cd77e",
    "moves": [
      {
        "index": 66,
        "before": [
          3744,
          1168,
          177,
          11
        ],
        "after": [
          3488,
          880,
          177,
          11
        ]
      },
      {
        "index": 67,
        "before": [
          3744,
          1200,
          178,
          11
        ],
        "after": [
          3488,
          912,
          178,
          11
        ]
      },
      {
        "index": 68,
        "before": [
          3744,
          1232,
          176,
          11
        ],
        "after": [
          3488,
          944,
          176,
          11
        ]
      },
      {
        "index": 71,
        "before": [
          3296,
          1072,
          177,
          11
        ],
        "after": [
          3168,
          1072,
          177,
          11
        ]
      },
      {
        "index": 72,
        "before": [
          3360,
          1072,
          178,
          11
        ],
        "after": [
          3232,
          1072,
          178,
          11
        ]
      },
      {
        "index": 73,
        "before": [
          3104,
          976,
          176,
          11
        ],
        "after": [
          3104,
          912,
          176,
          11
        ]
      },
      {
        "index": 76,
        "before": [
          3232,
          1072,
          177,
          11
        ],
        "after": [
          3104,
          1008,
          177,
          11
        ]
      },
      {
        "index": 77,
        "before": [
          3744,
          1264,
          177,
          11
        ],
        "after": [
          3488,
          976,
          177,
          11
        ]
      },
      {
        "index": 78,
        "before": [
          3680,
          1328,
          177,
          11
        ],
        "after": [
          3424,
          1072,
          177,
          11
        ]
      },
      {
        "index": 80,
        "before": [
          3616,
          1328,
          176,
          11
        ],
        "after": [
          3360,
          1072,
          176,
          11
        ]
      },
      {
        "index": 81,
        "before": [
          3168,
          1072,
          178,
          11
        ],
        "after": [
          3104,
          1040,
          178,
          11
        ]
      },
      {
        "index": 82,
        "before": [
          3104,
          1008,
          178,
          11
        ],
        "after": [
          3104,
          944,
          178,
          11
        ]
      },
      {
        "index": 84,
        "before": [
          3104,
          1040,
          177,
          11
        ],
        "after": [
          3104,
          976,
          177,
          11
        ]
      },
      {
        "index": 88,
        "before": [
          3552,
          1328,
          178,
          11
        ],
        "after": [
          3296,
          1072,
          178,
          11
        ]
      },
      {
        "index": 95,
        "before": [
          3072,
          864,
          149,
          0
        ],
        "after": [
          3296,
          736,
          149,
          0
        ]
      }
    ],
    "groups": [
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 191,
          "center": [
            3296,
            912
          ],
          "depot_type": 132,
          "owner": 0,
          "top_left_tile": [
            101,
            27
          ]
        },
        "mineral_indices": [
          82,
          81,
          84,
          72,
          71,
          76,
          73,
          78,
          80,
          77,
          68,
          67,
          88,
          66
        ],
        "gas_indices": [
          95
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 2
        },
        "parent_site_index": 0,
        "group_index": 0,
        "group_sizes": [
          14
        ],
        "source_anchor": [
          3296,
          912
        ],
        "planned_depot_sites": [],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "maximum_minerals": 14,
        "placement_policy": "reviewed_playtest_layout"
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 38,
          "center": [
            736,
            496
          ],
          "depot_type": 154,
          "owner": 1,
          "top_left_tile": [
            21,
            14
          ]
        },
        "mineral_indices": [
          6,
          5,
          7,
          15,
          12,
          20,
          13,
          21,
          4,
          8,
          14,
          22
        ],
        "gas_indices": [
          34
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 3
        },
        "parent_site_index": 1,
        "group_index": 0,
        "group_sizes": [
          12
        ],
        "source_anchor": [
          736,
          496
        ],
        "planned_depot_sites": [],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      }
    ]
  },
  "307": {
    "input_unit_sha256": "25b69c72a3aaaeebaf9c7bf72256fee3628a6ea570f29c22e3bb8c70900a2ee3",
    "moves": [
      {
        "index": 0,
        "before": [
          672,
          528,
          177,
          11
        ],
        "after": [
          384,
          80,
          177,
          11
        ]
      },
      {
        "index": 1,
        "before": [
          672,
          496,
          177,
          11
        ],
        "after": [
          448,
          80,
          177,
          11
        ]
      },
      {
        "index": 2,
        "before": [
          672,
          560,
          176,
          11
        ],
        "after": [
          96,
          208,
          176,
          11
        ]
      },
      {
        "index": 3,
        "before": [
          2720,
          144,
          178,
          11
        ],
        "after": [
          2720,
          80,
          178,
          11
        ]
      },
      {
        "index": 4,
        "before": [
          2720,
          208,
          176,
          11
        ],
        "after": [
          2720,
          144,
          176,
          11
        ]
      },
      {
        "index": 6,
        "before": [
          416,
          80,
          176,
          11
        ],
        "after": [
          192,
          80,
          176,
          11
        ]
      },
      {
        "index": 7,
        "before": [
          288,
          80,
          177,
          11
        ],
        "after": [
          96,
          176,
          177,
          11
        ]
      },
      {
        "index": 8,
        "before": [
          224,
          80,
          177,
          11
        ],
        "after": [
          96,
          144,
          177,
          11
        ]
      },
      {
        "index": 9,
        "before": [
          352,
          80,
          178,
          11
        ],
        "after": [
          128,
          80,
          178,
          11
        ]
      },
      {
        "index": 10,
        "before": [
          2720,
          80,
          177,
          11
        ],
        "after": [
          2656,
          48,
          177,
          11
        ]
      },
      {
        "index": 11,
        "before": [
          2336,
          464,
          178,
          11
        ],
        "after": [
          2528,
          48,
          178,
          11
        ]
      },
      {
        "index": 13,
        "before": [
          2336,
          496,
          176,
          11
        ],
        "after": [
          2464,
          48,
          176,
          11
        ]
      },
      {
        "index": 14,
        "before": [
          608,
          656,
          178,
          11
        ],
        "after": [
          96,
          272,
          178,
          11
        ]
      },
      {
        "index": 15,
        "before": [
          2720,
          112,
          176,
          11
        ],
        "after": [
          2592,
          48,
          176,
          11
        ]
      },
      {
        "index": 16,
        "before": [
          2720,
          272,
          177,
          11
        ],
        "after": [
          2720,
          208,
          177,
          11
        ]
      },
      {
        "index": 17,
        "before": [
          2592,
          624,
          177,
          11
        ],
        "after": [
          2720,
          240,
          177,
          11
        ]
      },
      {
        "index": 19,
        "before": [
          544,
          656,
          177,
          11
        ],
        "after": [
          96,
          304,
          177,
          11
        ]
      },
      {
        "index": 21,
        "before": [
          2400,
          624,
          177,
          11
        ],
        "after": [
          2656,
          368,
          177,
          11
        ]
      },
      {
        "index": 22,
        "before": [
          2464,
          624,
          178,
          11
        ],
        "after": [
          2720,
          304,
          178,
          11
        ]
      },
      {
        "index": 23,
        "before": [
          2336,
          560,
          176,
          11
        ],
        "after": [
          2528,
          368,
          176,
          11
        ]
      },
      {
        "index": 25,
        "before": [
          2720,
          176,
          178,
          11
        ],
        "after": [
          2720,
          112,
          178,
          11
        ]
      },
      {
        "index": 26,
        "before": [
          480,
          656,
          176,
          11
        ],
        "after": [
          96,
          336,
          176,
          11
        ]
      },
      {
        "index": 28,
        "before": [
          2752,
          240,
          178,
          11
        ],
        "after": [
          2720,
          176,
          178,
          11
        ]
      },
      {
        "index": 29,
        "before": [
          2336,
          528,
          178,
          11
        ],
        "after": [
          2592,
          368,
          178,
          11
        ]
      },
      {
        "index": 31,
        "before": [
          480,
          112,
          176,
          11
        ],
        "after": [
          320,
          80,
          176,
          11
        ]
      },
      {
        "index": 33,
        "before": [
          2528,
          624,
          178,
          11
        ],
        "after": [
          2720,
          272,
          178,
          11
        ]
      },
      {
        "index": 34,
        "before": [
          480,
          144,
          177,
          11
        ],
        "after": [
          256,
          80,
          177,
          11
        ]
      },
      {
        "index": 41,
        "before": [
          672,
          592,
          178,
          11
        ],
        "after": [
          96,
          240,
          178,
          11
        ]
      },
      {
        "index": 47,
        "before": [
          2752,
          384,
          188,
          11
        ],
        "after": [
          2432,
          480,
          188,
          11
        ]
      },
      {
        "index": 50,
        "before": [
          256,
          416,
          157,
          7
        ],
        "after": [
          288,
          416,
          157,
          7
        ]
      },
      {
        "index": 311,
        "before": [
          3520,
          3648,
          157,
          4
        ],
        "after": [
          3776,
          3840,
          157,
          4
        ]
      },
      {
        "index": 327,
        "before": [
          3232,
          4080,
          176,
          11
        ],
        "after": [
          3264,
          4016,
          176,
          11
        ]
      },
      {
        "index": 335,
        "before": [
          3744,
          3824,
          177,
          11
        ],
        "after": [
          3456,
          3632,
          177,
          11
        ]
      },
      {
        "index": 336,
        "before": [
          3008,
          4016,
          177,
          11
        ],
        "after": [
          3296,
          3728,
          177,
          11
        ]
      },
      {
        "index": 342,
        "before": [
          3296,
          4080,
          178,
          11
        ],
        "after": [
          3264,
          3984,
          178,
          11
        ]
      },
      {
        "index": 343,
        "before": [
          3776,
          3888,
          176,
          11
        ],
        "after": [
          3584,
          3632,
          176,
          11
        ]
      },
      {
        "index": 344,
        "before": [
          3744,
          3856,
          178,
          11
        ],
        "after": [
          3520,
          3632,
          178,
          11
        ]
      },
      {
        "index": 349,
        "before": [
          3776,
          3920,
          178,
          11
        ],
        "after": [
          3392,
          3664,
          178,
          11
        ]
      },
      {
        "index": 350,
        "before": [
          3168,
          4080,
          176,
          11
        ],
        "after": [
          3264,
          3952,
          176,
          11
        ]
      },
      {
        "index": 355,
        "before": [
          3040,
          4080,
          178,
          11
        ],
        "after": [
          3264,
          3824,
          178,
          11
        ]
      },
      {
        "index": 357,
        "before": [
          3008,
          4048,
          178,
          11
        ],
        "after": [
          3200,
          3760,
          178,
          11
        ]
      },
      {
        "index": 359,
        "before": [
          3744,
          3984,
          177,
          11
        ],
        "after": [
          3296,
          4080,
          177,
          11
        ]
      },
      {
        "index": 360,
        "before": [
          3712,
          4048,
          177,
          11
        ],
        "after": [
          3296,
          4048,
          177,
          11
        ]
      },
      {
        "index": 361,
        "before": [
          3104,
          4080,
          178,
          11
        ],
        "after": [
          3264,
          3920,
          178,
          11
        ]
      },
      {
        "index": 404,
        "before": [
          512,
          256,
          188,
          11
        ],
        "after": [
          416,
          416,
          188,
          11
        ]
      }
    ],
    "groups": [
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            2528,
            208
          ],
          "depot_type": 154,
          "owner": null,
          "top_left_tile": [
            77,
            5
          ]
        },
        "mineral_indices": [
          4,
          10,
          15,
          3,
          16,
          28,
          25,
          21,
          23,
          29,
          22,
          33,
          13,
          17,
          11
        ],
        "gas_indices": [
          47
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 25,
          "gas_exit": 13,
          "gas_lane": 80,
          "gas_inside_bank": 19,
          "depot_clearance": 82
        },
        "parent_site_index": 0,
        "group_index": 0,
        "group_sizes": [
          15
        ],
        "source_anchor": [
          2528,
          144
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              2528,
              208
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              77,
              5
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "maximum_minerals": 15,
        "placement_policy": "reviewed_playtest_layout"
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 35,
          "center": [
            288,
            240
          ],
          "depot_type": 154,
          "owner": 7,
          "top_left_tile": [
            7,
            6
          ]
        },
        "mineral_indices": [
          31,
          34,
          8,
          7,
          9,
          6,
          41,
          26,
          19,
          14,
          2,
          0,
          1
        ],
        "gas_indices": [
          50,
          404
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "resource_overlap": 6
        },
        "parent_site_index": 1,
        "group_index": 0,
        "group_sizes": [
          13
        ],
        "source_anchor": [
          288,
          240
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              2528,
              208
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              77,
              5
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "maximum_minerals": 13,
        "placement_policy": "reviewed_playtest_layout"
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 353,
          "center": [
            3520,
            3920
          ],
          "depot_type": 154,
          "owner": 4,
          "top_left_tile": [
            108,
            121
          ]
        },
        "mineral_indices": [
          359,
          360,
          343,
          344,
          349,
          335,
          357,
          342,
          327,
          350,
          336,
          355,
          361
        ],
        "gas_indices": [
          311
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 34,
          "geometry": 38
        },
        "parent_site_index": 2,
        "group_index": 0,
        "group_sizes": [
          13
        ],
        "source_anchor": [
          3520,
          3920
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              2528,
              208
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              77,
              5
            ]
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "maximum_minerals": 13,
        "placement_policy": "reviewed_playtest_layout"
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 116,
          "center": [
            3648,
            1520
          ],
          "depot_type": 154,
          "owner": 0,
          "top_left_tile": [
            112,
            46
          ]
        },
        "mineral_indices": [
          121,
          120,
          124,
          130,
          133,
          139,
          131,
          140,
          117,
          125,
          134,
          143
        ],
        "gas_indices": [
          108
        ],
        "status": "ladder_separate_gas",
        "reasons": {},
        "parent_site_index": 3,
        "group_index": 0,
        "group_sizes": [
          12
        ],
        "source_anchor": [
          3648,
          1520
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              2528,
              208
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              77,
              5
            ]
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 244,
          "center": [
            576,
            3056
          ],
          "depot_type": 154,
          "owner": 0,
          "top_left_tile": [
            16,
            94
          ]
        },
        "mineral_indices": [
          277,
          258,
          286,
          287,
          270,
          271,
          276,
          283,
          262,
          293,
          263
        ],
        "gas_indices": [
          282
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 56
        },
        "parent_site_index": 4,
        "group_index": 0,
        "group_sizes": [
          11
        ],
        "source_anchor": [
          576,
          3056
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              2528,
              208
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              77,
              5
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      }
    ]
  },
  "309": {
    "input_unit_sha256": "0b25d16c8eff04f2aaca0fd5e47d9f17d5e51e907a0f9ed1abd36d732b2103d3",
    "moves": [
      {
        "index": 211,
        "before": [
          2752,
          3792,
          177,
          11
        ],
        "after": [
          2752,
          3632,
          177,
          11
        ]
      },
      {
        "index": 219,
        "before": [
          2688,
          3792,
          177,
          11
        ],
        "after": [
          2688,
          3632,
          177,
          11
        ]
      },
      {
        "index": 226,
        "before": [
          2816,
          3792,
          176,
          11
        ],
        "after": [
          2816,
          3632,
          176,
          11
        ]
      },
      {
        "index": 228,
        "before": [
          2880,
          3792,
          178,
          11
        ],
        "after": [
          2880,
          3632,
          178,
          11
        ]
      },
      {
        "index": 231,
        "before": [
          2944,
          3792,
          176,
          11
        ],
        "after": [
          2944,
          3632,
          176,
          11
        ]
      },
      {
        "index": 232,
        "before": [
          3008,
          3888,
          178,
          11
        ],
        "after": [
          3008,
          3760,
          178,
          11
        ]
      },
      {
        "index": 234,
        "before": [
          3008,
          3824,
          176,
          11
        ],
        "after": [
          3008,
          3696,
          176,
          11
        ]
      },
      {
        "index": 236,
        "before": [
          3008,
          3856,
          178,
          11
        ],
        "after": [
          3008,
          3728,
          178,
          11
        ]
      },
      {
        "index": 239,
        "before": [
          3008,
          3920,
          178,
          11
        ],
        "after": [
          3008,
          3792,
          178,
          11
        ]
      },
      {
        "index": 388,
        "before": [
          3168,
          3968,
          188,
          11
        ],
        "after": [
          2816,
          3968,
          188,
          11
        ]
      },
      {
        "index": 389,
        "before": [
          3168,
          4032,
          188,
          11
        ],
        "after": [
          2976,
          3968,
          188,
          11
        ]
      }
    ],
    "groups": [
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            352,
            3888
          ],
          "depot_type": 154,
          "owner": null,
          "top_left_tile": [
            9,
            120
          ]
        },
        "mineral_indices": [
          218,
          202,
          212,
          238,
          225,
          229,
          220,
          237,
          203,
          230,
          208,
          233
        ],
        "gas_indices": [
          199
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "gas_inside_bank": 6
        },
        "parent_site_index": 0,
        "group_index": 0,
        "group_sizes": [
          12
        ],
        "source_anchor": [
          352,
          3888
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              352,
              3888
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              9,
              120
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2816,
              3792
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              86,
              117
            ]
          },
          {
            "kind": "expansion",
            "center": [
              96,
              1584
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              1,
              48
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3680,
              3024
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              113,
              93
            ]
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            2816,
            3792
          ],
          "depot_type": 154,
          "owner": null,
          "top_left_tile": [
            86,
            117
          ]
        },
        "mineral_indices": [
          226,
          234,
          236,
          231,
          232,
          228,
          239,
          211,
          219
        ],
        "gas_indices": [
          388,
          389
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "resource_overlap": 131,
          "gas_lane": 74,
          "plateau": 3,
          "gas_exit": 8
        },
        "parent_site_index": 1,
        "group_index": 0,
        "group_sizes": [
          9
        ],
        "source_anchor": [
          2816,
          3952
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              352,
              3888
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              9,
              120
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2816,
              3792
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              86,
              117
            ]
          },
          {
            "kind": "expansion",
            "center": [
              96,
              1584
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              1,
              48
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3680,
              3024
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              113,
              93
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "maximum_minerals": 12,
        "placement_policy": "reviewed_playtest_layout"
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 244,
          "center": [
            832,
            112
          ],
          "depot_type": 133,
          "owner": 5,
          "top_left_tile": [
            24,
            2
          ]
        },
        "mineral_indices": [
          2,
          4,
          10,
          11,
          8,
          1,
          15,
          7,
          9,
          0,
          3
        ],
        "gas_indices": [
          22,
          44
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 33,
          "geometry": 23,
          "resource_overlap": 322,
          "gas_lane": 239,
          "gas_inside_bank": 3,
          "gas_exit": 3
        },
        "parent_site_index": 2,
        "group_index": 0,
        "group_sizes": [
          11
        ],
        "source_anchor": [
          832,
          112
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              352,
              3888
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              9,
              120
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2816,
              3792
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              86,
              117
            ]
          },
          {
            "kind": "expansion",
            "center": [
              96,
              1584
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              1,
              48
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3680,
              3024
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              113,
              93
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            96,
            1584
          ],
          "depot_type": 154,
          "owner": null,
          "top_left_tile": [
            1,
            48
          ]
        },
        "mineral_indices": [
          74,
          75,
          78,
          77,
          79,
          76,
          80
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {},
        "parent_site_index": 3,
        "group_index": 0,
        "group_sizes": [
          7
        ],
        "source_anchor": [
          96,
          1584
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              352,
              3888
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              9,
              120
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2816,
              3792
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              86,
              117
            ]
          },
          {
            "kind": "expansion",
            "center": [
              96,
              1584
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              1,
              48
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3680,
              3024
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              113,
              93
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            3680,
            3024
          ],
          "depot_type": 154,
          "owner": null,
          "top_left_tile": [
            113,
            93
          ]
        },
        "mineral_indices": [
          189,
          185,
          190,
          192,
          191,
          194,
          195
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 1
        },
        "parent_site_index": 4,
        "group_index": 0,
        "group_sizes": [
          7
        ],
        "source_anchor": [
          3680,
          3024
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              352,
              3888
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              9,
              120
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2816,
              3792
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              86,
              117
            ]
          },
          {
            "kind": "expansion",
            "center": [
              96,
              1584
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              1,
              48
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3680,
              3024
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              113,
              93
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 245,
          "center": [
            2464,
            112
          ],
          "depot_type": 133,
          "owner": 6,
          "top_left_tile": [
            75,
            2
          ]
        },
        "mineral_indices": [
          55,
          5,
          51,
          48,
          13,
          12,
          54,
          14,
          50,
          6
        ],
        "gas_indices": [
          17,
          29
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 29,
          "geometry": 25,
          "resource_overlap": 138,
          "gas_lane": 70
        },
        "parent_site_index": 5,
        "group_index": 0,
        "group_sizes": [
          10
        ],
        "source_anchor": [
          2464,
          112
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              352,
              3888
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              9,
              120
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2816,
              3792
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              86,
              117
            ]
          },
          {
            "kind": "expansion",
            "center": [
              96,
              1584
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              1,
              48
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3680,
              3024
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              113,
              93
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 315,
          "center": [
            4000,
            2032
          ],
          "depot_type": 132,
          "owner": 0,
          "top_left_tile": [
            123,
            62
          ]
        },
        "mineral_indices": [
          101,
          104,
          105,
          100
        ],
        "gas_indices": [
          109
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 2,
          "geometry": 1
        },
        "parent_site_index": 6,
        "group_index": 0,
        "group_sizes": [
          4
        ],
        "source_anchor": [
          4000,
          2032
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              352,
              3888
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              9,
              120
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2816,
              3792
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              86,
              117
            ]
          },
          {
            "kind": "expansion",
            "center": [
              96,
              1584
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              1,
              48
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3680,
              3024
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              113,
              93
            ]
          }
        ],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 330,
          "center": [
            224,
            2416
          ],
          "depot_type": 133,
          "owner": 0,
          "top_left_tile": [
            5,
            74
          ]
        },
        "mineral_indices": [
          128,
          126,
          129
        ],
        "gas_indices": [
          169
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 4,
          "geometry": 4
        },
        "parent_site_index": 7,
        "group_index": 0,
        "group_sizes": [
          3
        ],
        "source_anchor": [
          224,
          2416
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              352,
              3888
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              9,
              120
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2816,
              3792
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              86,
              117
            ]
          },
          {
            "kind": "expansion",
            "center": [
              96,
              1584
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              1,
              48
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3680,
              3024
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              113,
              93
            ]
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      }
    ]
  },
  "310": {
    "input_unit_sha256": "dc221000c67dedcf724a0a91b1db4df1ba2ceb3773c57a1f397de56a8ee6bf75",
    "moves": [
      {
        "index": 49,
        "before": [
          1696,
          2608,
          176,
          11
        ],
        "after": [
          1824,
          2480,
          176,
          11
        ]
      },
      {
        "index": 61,
        "before": [
          1824,
          2416,
          178,
          11
        ],
        "after": [
          1824,
          2384,
          178,
          11
        ]
      },
      {
        "index": 64,
        "before": [
          1888,
          2544,
          176,
          11
        ],
        "after": [
          2208,
          2416,
          176,
          11
        ]
      },
      {
        "index": 65,
        "before": [
          2080,
          2544,
          177,
          11
        ],
        "after": [
          2208,
          2512,
          177,
          11
        ]
      },
      {
        "index": 72,
        "before": [
          2016,
          2544,
          178,
          11
        ],
        "after": [
          2208,
          2352,
          178,
          11
        ]
      },
      {
        "index": 73,
        "before": [
          1792,
          2864,
          178,
          11
        ],
        "after": [
          2208,
          2480,
          178,
          11
        ]
      },
      {
        "index": 74,
        "before": [
          1728,
          2864,
          177,
          11
        ],
        "after": [
          2080,
          2544,
          177,
          11
        ]
      },
      {
        "index": 76,
        "before": [
          2240,
          2368,
          149,
          0
        ],
        "after": [
          2112,
          2208,
          149,
          0
        ]
      },
      {
        "index": 77,
        "before": [
          1760,
          2544,
          177,
          11
        ],
        "after": [
          1824,
          2448,
          177,
          11
        ]
      },
      {
        "index": 78,
        "before": [
          1824,
          2384,
          176,
          11
        ],
        "after": [
          2208,
          2448,
          176,
          11
        ]
      },
      {
        "index": 82,
        "before": [
          1824,
          2448,
          177,
          11
        ],
        "after": [
          1824,
          2416,
          177,
          11
        ]
      },
      {
        "index": 83,
        "before": [
          1952,
          2544,
          178,
          11
        ],
        "after": [
          2208,
          2384,
          178,
          11
        ]
      },
      {
        "index": 84,
        "before": [
          1696,
          2704,
          176,
          11
        ],
        "after": [
          1824,
          2512,
          176,
          11
        ]
      },
      {
        "index": 90,
        "before": [
          1696,
          2736,
          177,
          11
        ],
        "after": [
          1952,
          2544,
          177,
          11
        ]
      },
      {
        "index": 91,
        "before": [
          1696,
          2768,
          178,
          11
        ],
        "after": [
          1888,
          2544,
          178,
          11
        ]
      },
      {
        "index": 99,
        "before": [
          1696,
          2800,
          176,
          11
        ],
        "after": [
          2016,
          2544,
          176,
          11
        ]
      },
      {
        "index": 123,
        "before": [
          2816,
          3088,
          177,
          11
        ],
        "after": [
          2560,
          3216,
          177,
          11
        ]
      },
      {
        "index": 124,
        "before": [
          2688,
          2768,
          176,
          11
        ],
        "after": [
          2560,
          3120,
          176,
          11
        ]
      },
      {
        "index": 125,
        "before": [
          2752,
          2768,
          178,
          11
        ],
        "after": [
          2560,
          3152,
          178,
          11
        ]
      },
      {
        "index": 126,
        "before": [
          2880,
          2768,
          178,
          11
        ],
        "after": [
          2688,
          3088,
          178,
          11
        ]
      },
      {
        "index": 127,
        "before": [
          2688,
          3088,
          177,
          11
        ],
        "after": [
          2560,
          3184,
          177,
          11
        ]
      },
      {
        "index": 128,
        "before": [
          2752,
          3088,
          177,
          11
        ],
        "after": [
          2560,
          3280,
          177,
          11
        ]
      },
      {
        "index": 129,
        "before": [
          2944,
          2832,
          177,
          11
        ],
        "after": [
          2880,
          3088,
          177,
          11
        ]
      },
      {
        "index": 130,
        "before": [
          2080,
          3552,
          149,
          3
        ],
        "after": [
          2304,
          3392,
          149,
          3
        ]
      },
      {
        "index": 131,
        "before": [
          2816,
          2768,
          176,
          11
        ],
        "after": [
          2624,
          3088,
          176,
          11
        ]
      },
      {
        "index": 132,
        "before": [
          2880,
          3088,
          178,
          11
        ],
        "after": [
          2560,
          3248,
          178,
          11
        ]
      },
      {
        "index": 133,
        "before": [
          2944,
          3184,
          178,
          11
        ],
        "after": [
          2944,
          3216,
          178,
          11
        ]
      },
      {
        "index": 136,
        "before": [
          2944,
          3216,
          177,
          11
        ],
        "after": [
          2944,
          3248,
          177,
          11
        ]
      },
      {
        "index": 137,
        "before": [
          2944,
          3248,
          177,
          11
        ],
        "after": [
          2944,
          3280,
          177,
          11
        ]
      },
      {
        "index": 138,
        "before": [
          2944,
          2864,
          176,
          11
        ],
        "after": [
          2816,
          3088,
          176,
          11
        ]
      },
      {
        "index": 139,
        "before": [
          2944,
          2896,
          177,
          11
        ],
        "after": [
          2752,
          3088,
          177,
          11
        ]
      },
      {
        "index": 144,
        "before": [
          2944,
          2928,
          178,
          11
        ],
        "after": [
          2944,
          3184,
          178,
          11
        ]
      },
      {
        "index": 173,
        "before": [
          2304,
          3856,
          176,
          11
        ],
        "after": [
          2112,
          3632,
          176,
          11
        ]
      },
      {
        "index": 177,
        "before": [
          2304,
          3728,
          177,
          11
        ],
        "after": [
          2112,
          3568,
          177,
          11
        ]
      },
      {
        "index": 178,
        "before": [
          2496,
          3568,
          177,
          11
        ],
        "after": [
          2112,
          3472,
          177,
          11
        ]
      },
      {
        "index": 181,
        "before": [
          2304,
          3824,
          178,
          11
        ],
        "after": [
          2112,
          3600,
          178,
          11
        ]
      },
      {
        "index": 182,
        "before": [
          2304,
          3920,
          176,
          11
        ],
        "after": [
          2272,
          3728,
          176,
          11
        ]
      },
      {
        "index": 183,
        "before": [
          2368,
          3728,
          177,
          11
        ],
        "after": [
          2112,
          3536,
          177,
          11
        ]
      },
      {
        "index": 184,
        "before": [
          2432,
          3728,
          176,
          11
        ],
        "after": [
          2400,
          3728,
          176,
          11
        ]
      },
      {
        "index": 185,
        "before": [
          2304,
          3888,
          177,
          11
        ],
        "after": [
          2336,
          3728,
          177,
          11
        ]
      },
      {
        "index": 186,
        "before": [
          2144,
          3984,
          178,
          11
        ],
        "after": [
          2112,
          3664,
          178,
          11
        ]
      },
      {
        "index": 188,
        "before": [
          2528,
          3264,
          149,
          3
        ],
        "after": [
          2784,
          3456,
          149,
          3
        ]
      },
      {
        "index": 189,
        "before": [
          2496,
          3600,
          178,
          11
        ],
        "after": [
          2112,
          3504,
          178,
          11
        ]
      },
      {
        "index": 190,
        "before": [
          2208,
          3984,
          177,
          11
        ],
        "after": [
          2144,
          3728,
          177,
          11
        ]
      },
      {
        "index": 191,
        "before": [
          2496,
          3632,
          176,
          11
        ],
        "after": [
          2464,
          3728,
          176,
          11
        ]
      },
      {
        "index": 193,
        "before": [
          2272,
          3984,
          178,
          11
        ],
        "after": [
          2208,
          3728,
          178,
          11
        ]
      }
    ],
    "groups": [
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            448,
            816
          ],
          "depot_type": 106,
          "owner": null,
          "top_left_tile": [
            12,
            24
          ],
          "scripted_starting_depot": true
        },
        "mineral_indices": [
          24,
          22,
          27,
          30,
          25,
          29,
          26,
          31,
          23
        ],
        "gas_indices": [
          15
        ],
        "status": "ladder_separate_gas",
        "reasons": {},
        "parent_site_index": 0,
        "group_index": 0,
        "group_sizes": [
          9,
          9
        ],
        "source_anchor": [
          448,
          816
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              448,
              816
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              12,
              24
            ]
          },
          {
            "kind": "expansion",
            "center": [
              192,
              1008
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              4,
              30
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              288,
              5744
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              7,
              178
            ]
          },
          {
            "kind": "expansion",
            "center": [
              288,
              6064
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              7,
              188
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              2784,
              368
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              85,
              10
            ]
          },
          {
            "kind": "expansion",
            "center": [
              5568,
              3824
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              172,
              118
            ]
          },
          {
            "kind": "expansion",
            "center": [
              1024,
              5680
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              30,
              176
            ]
          },
          {
            "kind": "expansion",
            "center": [
              768,
              5488
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              22,
              170
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              768,
              5872
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              22,
              182
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1056,
              2320
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              31,
              71
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2752,
              5104
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              84,
              158
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2848,
              1968
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              87,
              60
            ]
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            192,
            1008
          ],
          "depot_type": 154,
          "owner": null,
          "top_left_tile": [
            4,
            30
          ],
          "additional_group_depot": true
        },
        "mineral_indices": [
          32,
          34,
          33,
          21,
          20,
          19,
          18,
          17,
          28
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 3,
          "plateau": 2
        },
        "parent_site_index": 0,
        "group_index": 1,
        "group_sizes": [
          9,
          9
        ],
        "source_anchor": [
          448,
          816
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              448,
              816
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              12,
              24
            ]
          },
          {
            "kind": "expansion",
            "center": [
              192,
              1008
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              4,
              30
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              288,
              5744
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              7,
              178
            ]
          },
          {
            "kind": "expansion",
            "center": [
              288,
              6064
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              7,
              188
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              2784,
              368
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              85,
              10
            ]
          },
          {
            "kind": "expansion",
            "center": [
              5568,
              3824
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              172,
              118
            ]
          },
          {
            "kind": "expansion",
            "center": [
              1024,
              5680
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              30,
              176
            ]
          },
          {
            "kind": "expansion",
            "center": [
              768,
              5488
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              22,
              170
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              768,
              5872
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              22,
              182
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1056,
              2320
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              31,
              71
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2752,
              5104
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              84,
              158
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2848,
              1968
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              87,
              60
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            288,
            5744
          ],
          "depot_type": 154,
          "owner": null,
          "top_left_tile": [
            7,
            178
          ]
        },
        "mineral_indices": [
          340,
          325,
          337,
          318,
          315,
          319,
          312,
          331
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 1
        },
        "parent_site_index": 1,
        "group_index": 0,
        "group_sizes": [
          8,
          8
        ],
        "source_anchor": [
          288,
          5744
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              448,
              816
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              12,
              24
            ]
          },
          {
            "kind": "expansion",
            "center": [
              192,
              1008
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              4,
              30
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              288,
              5744
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              7,
              178
            ]
          },
          {
            "kind": "expansion",
            "center": [
              288,
              6064
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              7,
              188
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              2784,
              368
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              85,
              10
            ]
          },
          {
            "kind": "expansion",
            "center": [
              5568,
              3824
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              172,
              118
            ]
          },
          {
            "kind": "expansion",
            "center": [
              1024,
              5680
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              30,
              176
            ]
          },
          {
            "kind": "expansion",
            "center": [
              768,
              5488
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              22,
              170
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              768,
              5872
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              22,
              182
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1056,
              2320
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              31,
              71
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2752,
              5104
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              84,
              158
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2848,
              1968
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              87,
              60
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            288,
            6064
          ],
          "depot_type": 154,
          "owner": null,
          "top_left_tile": [
            7,
            188
          ],
          "additional_group_depot": true
        },
        "mineral_indices": [
          330,
          309,
          323,
          338,
          332,
          324,
          316,
          314
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 15,
          "plateau": 16
        },
        "parent_site_index": 1,
        "group_index": 1,
        "group_sizes": [
          8,
          8
        ],
        "source_anchor": [
          288,
          5744
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              448,
              816
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              12,
              24
            ]
          },
          {
            "kind": "expansion",
            "center": [
              192,
              1008
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              4,
              30
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              288,
              5744
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              7,
              178
            ]
          },
          {
            "kind": "expansion",
            "center": [
              288,
              6064
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              7,
              188
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              2784,
              368
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              85,
              10
            ]
          },
          {
            "kind": "expansion",
            "center": [
              5568,
              3824
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              172,
              118
            ]
          },
          {
            "kind": "expansion",
            "center": [
              1024,
              5680
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              30,
              176
            ]
          },
          {
            "kind": "expansion",
            "center": [
              768,
              5488
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              22,
              170
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              768,
              5872
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              22,
              182
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1056,
              2320
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              31,
              71
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2752,
              5104
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              84,
              158
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2848,
              1968
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              87,
              60
            ]
          }
        ],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 354,
          "center": [
            2016,
            2384
          ],
          "depot_type": 133,
          "owner": 0,
          "top_left_tile": [
            61,
            73
          ]
        },
        "mineral_indices": [
          72,
          82,
          61,
          64,
          65,
          78,
          83,
          91,
          99,
          74,
          90,
          84,
          73,
          49,
          77
        ],
        "gas_indices": [
          76
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 2
        },
        "parent_site_index": 2,
        "group_index": 0,
        "group_sizes": [
          15
        ],
        "source_anchor": [
          2016,
          2384
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              448,
              816
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              12,
              24
            ]
          },
          {
            "kind": "expansion",
            "center": [
              192,
              1008
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              4,
              30
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              288,
              5744
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              7,
              178
            ]
          },
          {
            "kind": "expansion",
            "center": [
              288,
              6064
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              7,
              188
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              2784,
              368
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              85,
              10
            ]
          },
          {
            "kind": "expansion",
            "center": [
              5568,
              3824
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              172,
              118
            ]
          },
          {
            "kind": "expansion",
            "center": [
              1024,
              5680
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              30,
              176
            ]
          },
          {
            "kind": "expansion",
            "center": [
              768,
              5488
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              22,
              170
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              768,
              5872
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              22,
              182
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1056,
              2320
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              31,
              71
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2752,
              5104
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              84,
              158
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2848,
              1968
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              87,
              60
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "maximum_minerals": 15,
        "placement_policy": "reviewed_playtest_layout"
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 369,
          "center": [
            2752,
            3248
          ],
          "depot_type": 133,
          "owner": 3,
          "top_left_tile": [
            84,
            100
          ]
        },
        "mineral_indices": [
          128,
          123,
          127,
          136,
          133,
          137,
          132,
          125,
          124,
          126,
          131,
          129,
          138,
          139,
          144
        ],
        "gas_indices": [
          188
        ],
        "status": "ladder_separate_gas",
        "reasons": {},
        "parent_site_index": 3,
        "group_index": 0,
        "group_sizes": [
          15
        ],
        "source_anchor": [
          2752,
          3248
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              448,
              816
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              12,
              24
            ]
          },
          {
            "kind": "expansion",
            "center": [
              192,
              1008
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              4,
              30
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              288,
              5744
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              7,
              178
            ]
          },
          {
            "kind": "expansion",
            "center": [
              288,
              6064
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              7,
              188
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              2784,
              368
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              85,
              10
            ]
          },
          {
            "kind": "expansion",
            "center": [
              5568,
              3824
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              172,
              118
            ]
          },
          {
            "kind": "expansion",
            "center": [
              1024,
              5680
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              30,
              176
            ]
          },
          {
            "kind": "expansion",
            "center": [
              768,
              5488
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              22,
              170
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              768,
              5872
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              22,
              182
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1056,
              2320
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              31,
              71
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2752,
              5104
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              84,
              158
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2848,
              1968
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              87,
              60
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "maximum_minerals": 15,
        "placement_policy": "reviewed_playtest_layout"
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 382,
          "center": [
            2304,
            3568
          ],
          "depot_type": 133,
          "owner": 3,
          "top_left_tile": [
            70,
            110
          ]
        },
        "mineral_indices": [
          189,
          184,
          191,
          177,
          178,
          183,
          190,
          186,
          182,
          185,
          193,
          173,
          181
        ],
        "gas_indices": [
          130
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 5,
          "depot_clearance": 48
        },
        "parent_site_index": 4,
        "group_index": 0,
        "group_sizes": [
          13
        ],
        "source_anchor": [
          2304,
          3568
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              448,
              816
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              12,
              24
            ]
          },
          {
            "kind": "expansion",
            "center": [
              192,
              1008
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              4,
              30
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              288,
              5744
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              7,
              178
            ]
          },
          {
            "kind": "expansion",
            "center": [
              288,
              6064
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              7,
              188
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              2784,
              368
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              85,
              10
            ]
          },
          {
            "kind": "expansion",
            "center": [
              5568,
              3824
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              172,
              118
            ]
          },
          {
            "kind": "expansion",
            "center": [
              1024,
              5680
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              30,
              176
            ]
          },
          {
            "kind": "expansion",
            "center": [
              768,
              5488
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              22,
              170
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              768,
              5872
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              22,
              182
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1056,
              2320
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              31,
              71
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2752,
              5104
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              84,
              158
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2848,
              1968
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              87,
              60
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "maximum_minerals": 13,
        "placement_policy": "reviewed_playtest_layout"
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 398,
          "center": [
            3520,
            4304
          ],
          "depot_type": 133,
          "owner": 0,
          "top_left_tile": [
            108,
            133
          ]
        },
        "mineral_indices": [
          255,
          254,
          262,
          252,
          251,
          261,
          250,
          260,
          248,
          249,
          253,
          263
        ],
        "gas_indices": [
          219
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 58,
          "gas_inside_bank": 4,
          "gas_exit": 1
        },
        "parent_site_index": 5,
        "group_index": 0,
        "group_sizes": [
          12
        ],
        "source_anchor": [
          3520,
          4304
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              448,
              816
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              12,
              24
            ]
          },
          {
            "kind": "expansion",
            "center": [
              192,
              1008
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              4,
              30
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              288,
              5744
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              7,
              178
            ]
          },
          {
            "kind": "expansion",
            "center": [
              288,
              6064
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              7,
              188
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              2784,
              368
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              85,
              10
            ]
          },
          {
            "kind": "expansion",
            "center": [
              5568,
              3824
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              172,
              118
            ]
          },
          {
            "kind": "expansion",
            "center": [
              1024,
              5680
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              30,
              176
            ]
          },
          {
            "kind": "expansion",
            "center": [
              768,
              5488
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              22,
              170
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              768,
              5872
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              22,
              182
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1056,
              2320
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              31,
              71
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2752,
              5104
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              84,
              158
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2848,
              1968
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              87,
              60
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            2784,
            368
          ],
          "depot_type": 154,
          "owner": null,
          "top_left_tile": [
            85,
            10
          ]
        },
        "mineral_indices": [
          2,
          1,
          3,
          8,
          7,
          9,
          6,
          10,
          0,
          5,
          12
        ],
        "gas_indices": [
          4
        ],
        "status": "ladder_separate_gas",
        "reasons": {},
        "parent_site_index": 6,
        "group_index": 0,
        "group_sizes": [
          11
        ],
        "source_anchor": [
          2784,
          368
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              448,
              816
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              12,
              24
            ]
          },
          {
            "kind": "expansion",
            "center": [
              192,
              1008
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              4,
              30
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              288,
              5744
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              7,
              178
            ]
          },
          {
            "kind": "expansion",
            "center": [
              288,
              6064
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              7,
              188
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              2784,
              368
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              85,
              10
            ]
          },
          {
            "kind": "expansion",
            "center": [
              5568,
              3824
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              172,
              118
            ]
          },
          {
            "kind": "expansion",
            "center": [
              1024,
              5680
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              30,
              176
            ]
          },
          {
            "kind": "expansion",
            "center": [
              768,
              5488
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              22,
              170
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              768,
              5872
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              22,
              182
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1056,
              2320
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              31,
              71
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2752,
              5104
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              84,
              158
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2848,
              1968
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              87,
              60
            ]
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            5568,
            3824
          ],
          "depot_type": 154,
          "owner": null,
          "top_left_tile": [
            172,
            118
          ]
        },
        "mineral_indices": [
          195,
          192,
          197,
          201,
          199,
          207,
          200,
          208,
          187,
          198,
          196
        ],
        "gas_indices": [
          217
        ],
        "status": "ladder_separate_gas",
        "reasons": {},
        "parent_site_index": 7,
        "group_index": 0,
        "group_sizes": [
          11
        ],
        "source_anchor": [
          5568,
          3824
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              448,
              816
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              12,
              24
            ]
          },
          {
            "kind": "expansion",
            "center": [
              192,
              1008
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              4,
              30
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              288,
              5744
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              7,
              178
            ]
          },
          {
            "kind": "expansion",
            "center": [
              288,
              6064
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              7,
              188
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              2784,
              368
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              85,
              10
            ]
          },
          {
            "kind": "expansion",
            "center": [
              5568,
              3824
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              172,
              118
            ]
          },
          {
            "kind": "expansion",
            "center": [
              1024,
              5680
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              30,
              176
            ]
          },
          {
            "kind": "expansion",
            "center": [
              768,
              5488
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              22,
              170
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              768,
              5872
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              22,
              182
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1056,
              2320
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              31,
              71
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2752,
              5104
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              84,
              158
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2848,
              1968
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              87,
              60
            ]
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            1024,
            5680
          ],
          "depot_type": 154,
          "owner": null,
          "top_left_tile": [
            30,
            176
          ]
        },
        "mineral_indices": [
          287,
          310,
          301,
          313,
          285,
          317,
          278,
          284,
          322
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {},
        "parent_site_index": 8,
        "group_index": 0,
        "group_sizes": [
          9,
          9,
          9
        ],
        "source_anchor": [
          1024,
          5680
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              448,
              816
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              12,
              24
            ]
          },
          {
            "kind": "expansion",
            "center": [
              192,
              1008
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              4,
              30
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              288,
              5744
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              7,
              178
            ]
          },
          {
            "kind": "expansion",
            "center": [
              288,
              6064
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              7,
              188
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              2784,
              368
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              85,
              10
            ]
          },
          {
            "kind": "expansion",
            "center": [
              5568,
              3824
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              172,
              118
            ]
          },
          {
            "kind": "expansion",
            "center": [
              1024,
              5680
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              30,
              176
            ]
          },
          {
            "kind": "expansion",
            "center": [
              768,
              5488
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              22,
              170
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              768,
              5872
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              22,
              182
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1056,
              2320
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              31,
              71
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2752,
              5104
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              84,
              158
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2848,
              1968
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              87,
              60
            ]
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            768,
            5488
          ],
          "depot_type": 154,
          "owner": null,
          "top_left_tile": [
            22,
            170
          ],
          "additional_group_depot": true
        },
        "mineral_indices": [
          283,
          299,
          279,
          291,
          280,
          305,
          302,
          344,
          343
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {},
        "parent_site_index": 8,
        "group_index": 1,
        "group_sizes": [
          9,
          9,
          9
        ],
        "source_anchor": [
          1024,
          5680
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              448,
              816
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              12,
              24
            ]
          },
          {
            "kind": "expansion",
            "center": [
              192,
              1008
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              4,
              30
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              288,
              5744
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              7,
              178
            ]
          },
          {
            "kind": "expansion",
            "center": [
              288,
              6064
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              7,
              188
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              2784,
              368
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              85,
              10
            ]
          },
          {
            "kind": "expansion",
            "center": [
              5568,
              3824
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              172,
              118
            ]
          },
          {
            "kind": "expansion",
            "center": [
              1024,
              5680
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              30,
              176
            ]
          },
          {
            "kind": "expansion",
            "center": [
              768,
              5488
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              22,
              170
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              768,
              5872
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              22,
              182
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1056,
              2320
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              31,
              71
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2752,
              5104
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              84,
              158
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2848,
              1968
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              87,
              60
            ]
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            768,
            5872
          ],
          "depot_type": 154,
          "owner": null,
          "top_left_tile": [
            22,
            182
          ],
          "additional_group_depot": true
        },
        "mineral_indices": [
          334,
          333,
          346,
          327,
          326,
          321,
          345,
          347,
          320
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {
          "depot_clearance": 1
        },
        "parent_site_index": 8,
        "group_index": 2,
        "group_sizes": [
          9,
          9,
          9
        ],
        "source_anchor": [
          1024,
          5680
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              448,
              816
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              12,
              24
            ]
          },
          {
            "kind": "expansion",
            "center": [
              192,
              1008
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              4,
              30
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              288,
              5744
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              7,
              178
            ]
          },
          {
            "kind": "expansion",
            "center": [
              288,
              6064
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              7,
              188
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              2784,
              368
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              85,
              10
            ]
          },
          {
            "kind": "expansion",
            "center": [
              5568,
              3824
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              172,
              118
            ]
          },
          {
            "kind": "expansion",
            "center": [
              1024,
              5680
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              30,
              176
            ]
          },
          {
            "kind": "expansion",
            "center": [
              768,
              5488
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              22,
              170
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              768,
              5872
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              22,
              182
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1056,
              2320
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              31,
              71
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2752,
              5104
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              84,
              158
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2848,
              1968
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              87,
              60
            ]
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            1056,
            2320
          ],
          "depot_type": 154,
          "owner": null,
          "top_left_tile": [
            31,
            71
          ]
        },
        "mineral_indices": [
          56,
          51,
          68,
          47,
          44,
          52,
          41,
          57,
          50,
          62
        ],
        "gas_indices": [
          69
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 1
        },
        "parent_site_index": 9,
        "group_index": 0,
        "group_sizes": [
          10
        ],
        "source_anchor": [
          1056,
          2320
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              448,
              816
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              12,
              24
            ]
          },
          {
            "kind": "expansion",
            "center": [
              192,
              1008
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              4,
              30
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              288,
              5744
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              7,
              178
            ]
          },
          {
            "kind": "expansion",
            "center": [
              288,
              6064
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              7,
              188
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              2784,
              368
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              85,
              10
            ]
          },
          {
            "kind": "expansion",
            "center": [
              5568,
              3824
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              172,
              118
            ]
          },
          {
            "kind": "expansion",
            "center": [
              1024,
              5680
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              30,
              176
            ]
          },
          {
            "kind": "expansion",
            "center": [
              768,
              5488
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              22,
              170
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              768,
              5872
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              22,
              182
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1056,
              2320
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              31,
              71
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2752,
              5104
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              84,
              158
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2848,
              1968
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              87,
              60
            ]
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 356,
          "center": [
            3552,
            2480
          ],
          "depot_type": 131,
          "owner": 0,
          "top_left_tile": [
            109,
            76
          ]
        },
        "mineral_indices": [
          75,
          88,
          87,
          93,
          80,
          94,
          67,
          79,
          86
        ],
        "gas_indices": [
          112
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 1,
          "plateau": 1
        },
        "parent_site_index": 10,
        "group_index": 0,
        "group_sizes": [
          9
        ],
        "source_anchor": [
          3552,
          2480
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              448,
              816
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              12,
              24
            ]
          },
          {
            "kind": "expansion",
            "center": [
              192,
              1008
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              4,
              30
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              288,
              5744
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              7,
              178
            ]
          },
          {
            "kind": "expansion",
            "center": [
              288,
              6064
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              7,
              188
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              2784,
              368
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              85,
              10
            ]
          },
          {
            "kind": "expansion",
            "center": [
              5568,
              3824
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              172,
              118
            ]
          },
          {
            "kind": "expansion",
            "center": [
              1024,
              5680
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              30,
              176
            ]
          },
          {
            "kind": "expansion",
            "center": [
              768,
              5488
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              22,
              170
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              768,
              5872
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              22,
              182
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1056,
              2320
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              31,
              71
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2752,
              5104
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              84,
              158
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2848,
              1968
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              87,
              60
            ]
          }
        ],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            2752,
            5104
          ],
          "depot_type": 154,
          "owner": null,
          "top_left_tile": [
            84,
            158
          ]
        },
        "mineral_indices": [
          273,
          272,
          274,
          269,
          268,
          270,
          267,
          271,
          275
        ],
        "gas_indices": [
          266
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 1,
          "gas_lane": 10
        },
        "parent_site_index": 11,
        "group_index": 0,
        "group_sizes": [
          9
        ],
        "source_anchor": [
          2752,
          5104
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              448,
              816
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              12,
              24
            ]
          },
          {
            "kind": "expansion",
            "center": [
              192,
              1008
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              4,
              30
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              288,
              5744
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              7,
              178
            ]
          },
          {
            "kind": "expansion",
            "center": [
              288,
              6064
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              7,
              188
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              2784,
              368
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              85,
              10
            ]
          },
          {
            "kind": "expansion",
            "center": [
              5568,
              3824
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              172,
              118
            ]
          },
          {
            "kind": "expansion",
            "center": [
              1024,
              5680
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              30,
              176
            ]
          },
          {
            "kind": "expansion",
            "center": [
              768,
              5488
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              22,
              170
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              768,
              5872
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              22,
              182
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1056,
              2320
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              31,
              71
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2752,
              5104
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              84,
              158
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2848,
              1968
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              87,
              60
            ]
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            2848,
            1968
          ],
          "depot_type": 154,
          "owner": null,
          "top_left_tile": [
            87,
            60
          ]
        },
        "mineral_indices": [
          53,
          46,
          48,
          42,
          40,
          43,
          39,
          45
        ],
        "gas_indices": [
          63
        ],
        "status": "ladder_separate_gas",
        "reasons": {},
        "parent_site_index": 12,
        "group_index": 0,
        "group_sizes": [
          8
        ],
        "source_anchor": [
          2848,
          1968
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              448,
              816
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              12,
              24
            ]
          },
          {
            "kind": "expansion",
            "center": [
              192,
              1008
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              4,
              30
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              288,
              5744
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              7,
              178
            ]
          },
          {
            "kind": "expansion",
            "center": [
              288,
              6064
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              7,
              188
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              2784,
              368
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              85,
              10
            ]
          },
          {
            "kind": "expansion",
            "center": [
              5568,
              3824
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              172,
              118
            ]
          },
          {
            "kind": "expansion",
            "center": [
              1024,
              5680
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              30,
              176
            ]
          },
          {
            "kind": "expansion",
            "center": [
              768,
              5488
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              22,
              170
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              768,
              5872
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              22,
              182
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1056,
              2320
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              31,
              71
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2752,
              5104
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              84,
              158
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2848,
              1968
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              87,
              60
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 401,
          "center": [
            1536,
            4336
          ],
          "depot_type": 131,
          "owner": 0,
          "top_left_tile": [
            46,
            134
          ]
        },
        "mineral_indices": [
          235,
          231,
          237,
          241,
          245,
          246,
          242
        ],
        "gas_indices": [
          259
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 16,
          "plateau": 16,
          "gas_lane": 2,
          "gas_exit": 1
        },
        "parent_site_index": 13,
        "group_index": 0,
        "group_sizes": [
          7
        ],
        "source_anchor": [
          1536,
          4336
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              448,
              816
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              12,
              24
            ]
          },
          {
            "kind": "expansion",
            "center": [
              192,
              1008
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              4,
              30
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              288,
              5744
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              7,
              178
            ]
          },
          {
            "kind": "expansion",
            "center": [
              288,
              6064
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              7,
              188
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              2784,
              368
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              85,
              10
            ]
          },
          {
            "kind": "expansion",
            "center": [
              5568,
              3824
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              172,
              118
            ]
          },
          {
            "kind": "expansion",
            "center": [
              1024,
              5680
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              30,
              176
            ]
          },
          {
            "kind": "expansion",
            "center": [
              768,
              5488
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              22,
              170
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              768,
              5872
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              22,
              182
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1056,
              2320
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              31,
              71
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2752,
              5104
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              84,
              158
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2848,
              1968
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              87,
              60
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 306,
          "center": [
            5376,
            5584
          ],
          "depot_type": 154,
          "owner": 1,
          "top_left_tile": [
            166,
            173
          ]
        },
        "mineral_indices": [
          295,
          294,
          298,
          286,
          282,
          290,
          281
        ],
        "gas_indices": [
          277,
          307
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "resource_overlap": 2
        },
        "parent_site_index": 14,
        "group_index": 0,
        "group_sizes": [
          7
        ],
        "source_anchor": [
          5376,
          5584
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              448,
              816
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              12,
              24
            ]
          },
          {
            "kind": "expansion",
            "center": [
              192,
              1008
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              4,
              30
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              288,
              5744
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              7,
              178
            ]
          },
          {
            "kind": "expansion",
            "center": [
              288,
              6064
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              7,
              188
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              2784,
              368
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              85,
              10
            ]
          },
          {
            "kind": "expansion",
            "center": [
              5568,
              3824
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              172,
              118
            ]
          },
          {
            "kind": "expansion",
            "center": [
              1024,
              5680
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              30,
              176
            ]
          },
          {
            "kind": "expansion",
            "center": [
              768,
              5488
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              22,
              170
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              768,
              5872
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              22,
              182
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1056,
              2320
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              31,
              71
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2752,
              5104
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              84,
              158
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2848,
              1968
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              87,
              60
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      }
    ]
  },
  "402": {
    "input_unit_sha256": "6728474c620d9001e92aab37d1538f8d756361ea4209275ce95e30e518c3efd4",
    "moves": [
      {
        "index": 128,
        "before": [
          192,
          2432,
          188,
          11
        ],
        "after": [
          192,
          2528,
          188,
          11
        ]
      }
    ],
    "groups": [
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            192,
            496
          ],
          "depot_type": 154,
          "owner": null,
          "top_left_tile": [
            4,
            14
          ]
        },
        "mineral_indices": [
          9,
          8,
          12,
          15,
          11,
          16,
          13,
          19,
          7,
          14,
          10
        ],
        "gas_indices": [
          20
        ],
        "status": "ladder_separate_gas",
        "reasons": {},
        "parent_site_index": 0,
        "group_index": 0,
        "group_sizes": [
          11
        ],
        "source_anchor": [
          192,
          496
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              192,
              496
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              4,
              14
            ]
          },
          {
            "kind": "expansion",
            "center": [
              192,
              2704
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              4,
              83
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3008,
              496
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              92,
              14
            ]
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            192,
            2704
          ],
          "depot_type": 154,
          "owner": null,
          "top_left_tile": [
            4,
            83
          ]
        },
        "mineral_indices": [
          122,
          131,
          123,
          126,
          119,
          125,
          127,
          132,
          118,
          130,
          135
        ],
        "gas_indices": [
          128
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 1
        },
        "parent_site_index": 1,
        "group_index": 0,
        "group_sizes": [
          11
        ],
        "source_anchor": [
          192,
          2704
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              192,
              496
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              4,
              14
            ]
          },
          {
            "kind": "expansion",
            "center": [
              192,
              2704
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              4,
              83
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3008,
              496
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              92,
              14
            ]
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 161,
          "center": [
            1504,
            2576
          ],
          "depot_type": 132,
          "owner": 4,
          "top_left_tile": [
            45,
            79
          ]
        },
        "mineral_indices": [
          104,
          94,
          99,
          102,
          86,
          83,
          91
        ],
        "gas_indices": [
          114
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 28,
          "plateau": 4
        },
        "parent_site_index": 2,
        "group_index": 0,
        "group_sizes": [
          7
        ],
        "source_anchor": [
          1504,
          2576
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              192,
              496
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              4,
              14
            ]
          },
          {
            "kind": "expansion",
            "center": [
              192,
              2704
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              4,
              83
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3008,
              496
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              92,
              14
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            3008,
            496
          ],
          "depot_type": 154,
          "owner": null,
          "top_left_tile": [
            92,
            14
          ]
        },
        "mineral_indices": [
          25,
          24,
          22,
          21,
          23
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 15,
          "geometry": 5
        },
        "parent_site_index": 3,
        "group_index": 0,
        "group_sizes": [
          5
        ],
        "source_anchor": [
          3008,
          496
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              192,
              496
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              4,
              14
            ]
          },
          {
            "kind": "expansion",
            "center": [
              192,
              2704
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              4,
              83
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3008,
              496
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              92,
              14
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      }
    ]
  },
  "403": {
    "input_unit_sha256": "820fd2ae43987b0aff7199e7fd4c16d679961934573121a6e3d70884ed9b16d9",
    "moves": [
      {
        "index": 0,
        "before": [
          800,
          560,
          176,
          11
        ],
        "after": [
          1024,
          496,
          176,
          11
        ]
      },
      {
        "index": 1,
        "before": [
          800,
          1024,
          188,
          11
        ],
        "after": [
          864,
          416,
          188,
          11
        ]
      },
      {
        "index": 2,
        "before": [
          800,
          528,
          177,
          11
        ],
        "after": [
          1088,
          496,
          177,
          11
        ]
      },
      {
        "index": 3,
        "before": [
          1056,
          560,
          177,
          11
        ],
        "after": [
          1184,
          656,
          177,
          11
        ]
      },
      {
        "index": 4,
        "before": [
          832,
          656,
          178,
          11
        ],
        "after": [
          1184,
          752,
          178,
          11
        ]
      },
      {
        "index": 6,
        "before": [
          864,
          560,
          178,
          11
        ],
        "after": [
          1184,
          720,
          178,
          11
        ]
      },
      {
        "index": 7,
        "before": [
          928,
          560,
          178,
          11
        ],
        "after": [
          1184,
          688,
          178,
          11
        ]
      },
      {
        "index": 8,
        "before": [
          1120,
          560,
          177,
          11
        ],
        "after": [
          1184,
          592,
          177,
          11
        ]
      },
      {
        "index": 9,
        "before": [
          992,
          560,
          178,
          11
        ],
        "after": [
          1184,
          624,
          178,
          11
        ]
      },
      {
        "index": 34,
        "before": [
          2320,
          1760,
          165,
          1
        ],
        "after": [
          2352,
          1920,
          165,
          1
        ]
      }
    ],
    "groups": [
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            992,
            656
          ],
          "depot_type": 154,
          "owner": null,
          "top_left_tile": [
            29,
            19
          ]
        },
        "mineral_indices": [
          5,
          7,
          8,
          4,
          9,
          0,
          3,
          6,
          2
        ],
        "gas_indices": [
          1
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 34,
          "geometry": 12
        },
        "parent_site_index": 0,
        "group_index": 0,
        "group_sizes": [
          9
        ],
        "source_anchor": [
          1024,
          720
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              992,
              656
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              29,
              19
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "maximum_minerals": 12,
        "placement_policy": "reviewed_playtest_layout"
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 25,
          "center": [
            2432,
            1648
          ],
          "depot_type": 154,
          "owner": 1,
          "top_left_tile": [
            74,
            50
          ]
        },
        "mineral_indices": [
          19,
          31,
          20,
          27,
          15,
          24,
          16,
          23,
          22
        ],
        "gas_indices": [
          14
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 15,
          "geometry": 25
        },
        "parent_site_index": 1,
        "group_index": 0,
        "group_sizes": [
          9
        ],
        "source_anchor": [
          2432,
          1648
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              992,
              656
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              29,
              19
            ]
          }
        ],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 157,
          "center": [
            256,
            2384
          ],
          "depot_type": 133,
          "owner": 3,
          "top_left_tile": [
            6,
            73
          ]
        },
        "mineral_indices": [
          67,
          62,
          71,
          53,
          49,
          57,
          63,
          56
        ],
        "gas_indices": [
          109
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 1
        },
        "parent_site_index": 2,
        "group_index": 0,
        "group_sizes": [
          8
        ],
        "source_anchor": [
          256,
          2384
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              992,
              656
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              29,
              19
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 167,
          "center": [
            832,
            2544
          ],
          "depot_type": 133,
          "owner": 4,
          "top_left_tile": [
            24,
            78
          ]
        },
        "mineral_indices": [
          125,
          121,
          116,
          120,
          110,
          126,
          128
        ],
        "gas_indices": [
          130
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 24,
          "plateau": 8,
          "gas_exit": 5,
          "gas_lane": 2,
          "trigger_region": 12
        },
        "parent_site_index": 3,
        "group_index": 0,
        "group_sizes": [
          7
        ],
        "source_anchor": [
          832,
          2544
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              992,
              656
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              29,
              19
            ]
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      }
    ]
  },
  "406": {
    "input_unit_sha256": "78bf80023bff3d5ac9ff927c0a607cc5601f6e73de341743fee1a19626f6ed89",
    "moves": [
      {
        "index": 3,
        "before": [
          2208,
          48,
          176,
          11
        ],
        "after": [
          2528,
          144,
          176,
          11
        ]
      },
      {
        "index": 5,
        "before": [
          2208,
          112,
          177,
          11
        ],
        "after": [
          2400,
          208,
          177,
          11
        ]
      },
      {
        "index": 6,
        "before": [
          2208,
          80,
          178,
          11
        ],
        "after": [
          2400,
          176,
          178,
          11
        ]
      },
      {
        "index": 12,
        "before": [
          2208,
          16,
          177,
          11
        ],
        "after": [
          2464,
          144,
          177,
          11
        ]
      },
      {
        "index": 14,
        "before": [
          2208,
          144,
          176,
          11
        ],
        "after": [
          2400,
          240,
          176,
          11
        ]
      },
      {
        "index": 19,
        "before": [
          2272,
          208,
          176,
          11
        ],
        "after": [
          2400,
          304,
          176,
          11
        ]
      },
      {
        "index": 20,
        "before": [
          2784,
          240,
          177,
          11
        ],
        "after": [
          2784,
          272,
          177,
          11
        ]
      },
      {
        "index": 21,
        "before": [
          2784,
          208,
          178,
          11
        ],
        "after": [
          2784,
          240,
          178,
          11
        ]
      },
      {
        "index": 27,
        "before": [
          2784,
          272,
          177,
          11
        ],
        "after": [
          2784,
          304,
          177,
          11
        ]
      },
      {
        "index": 28,
        "before": [
          2784,
          304,
          176,
          11
        ],
        "after": [
          2784,
          336,
          176,
          11
        ]
      },
      {
        "index": 31,
        "before": [
          2208,
          176,
          178,
          11
        ],
        "after": [
          2400,
          272,
          178,
          11
        ]
      },
      {
        "index": 38,
        "before": [
          2208,
          208,
          178,
          11
        ],
        "after": [
          2400,
          336,
          178,
          11
        ]
      },
      {
        "index": 683,
        "before": [
          2368,
          288,
          188,
          11
        ],
        "after": [
          2592,
          480,
          188,
          11
        ]
      },
      {
        "index": 684,
        "before": [
          2368,
          224,
          188,
          11
        ],
        "after": [
          2816,
          448,
          188,
          11
        ]
      }
    ],
    "groups": [
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 58,
          "center": [
            2592,
            304
          ],
          "depot_type": 154,
          "owner": 1,
          "top_left_tile": [
            79,
            8
          ]
        },
        "mineral_indices": [
          20,
          4,
          21,
          27,
          22,
          28,
          13,
          3,
          5,
          14,
          12,
          6,
          31,
          38,
          19
        ],
        "gas_indices": [
          683,
          684
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "resource_overlap": 167,
          "depot_clearance": 412,
          "geometry": 4,
          "gas_exit": 1
        },
        "parent_site_index": 0,
        "group_index": 0,
        "group_sizes": [
          15
        ],
        "source_anchor": [
          2592,
          304
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              3840,
              1392
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              118,
              42
            ]
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "maximum_minerals": 15,
        "placement_policy": "reviewed_playtest_layout"
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 426,
          "center": [
            384,
            240
          ],
          "depot_type": 131,
          "owner": 4,
          "top_left_tile": [
            10,
            6
          ]
        },
        "mineral_indices": [
          8,
          0,
          7,
          1,
          2,
          9,
          16,
          10,
          15
        ],
        "gas_indices": [
          48
        ],
        "status": "ladder_separate_gas",
        "reasons": {},
        "parent_site_index": 1,
        "group_index": 0,
        "group_sizes": [
          9
        ],
        "source_anchor": [
          384,
          240
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              3840,
              1392
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              118,
              42
            ]
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 525,
          "center": [
            768,
            2768
          ],
          "depot_type": 133,
          "owner": 4,
          "top_left_tile": [
            22,
            85
          ]
        },
        "mineral_indices": [
          262,
          251,
          240,
          235,
          246,
          226,
          250,
          217
        ],
        "gas_indices": [
          287
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 9,
          "geometry": 27
        },
        "parent_site_index": 2,
        "group_index": 0,
        "group_sizes": [
          8
        ],
        "source_anchor": [
          768,
          2768
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              3840,
              1392
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              118,
              42
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 584,
          "center": [
            2208,
            3824
          ],
          "depot_type": 133,
          "owner": 5,
          "top_left_tile": [
            67,
            118
          ]
        },
        "mineral_indices": [
          350,
          344,
          357,
          387,
          370,
          395,
          364,
          408
        ],
        "gas_indices": [
          421
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 3
        },
        "parent_site_index": 3,
        "group_index": 0,
        "group_sizes": [
          8
        ],
        "source_anchor": [
          2208,
          3824
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              3840,
              1392
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              118,
              42
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 522,
          "center": [
            1888,
            2768
          ],
          "depot_type": 132,
          "owner": 5,
          "top_left_tile": [
            57,
            85
          ]
        },
        "mineral_indices": [
          257,
          269,
          270,
          279,
          281,
          280
        ],
        "gas_indices": [
          266
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 5
        },
        "parent_site_index": 4,
        "group_index": 0,
        "group_sizes": [
          6
        ],
        "source_anchor": [
          1888,
          2768
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              3840,
              1392
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              118,
              42
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 427,
          "center": [
            3616,
            272
          ],
          "depot_type": 131,
          "owner": 3,
          "top_left_tile": [
            111,
            7
          ]
        },
        "mineral_indices": [
          54,
          57,
          37,
          18,
          42
        ],
        "gas_indices": [
          11
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 4
        },
        "parent_site_index": 5,
        "group_index": 0,
        "group_sizes": [
          5
        ],
        "source_anchor": [
          3616,
          272
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              3840,
              1392
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              118,
              42
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 590,
          "center": [
            832,
            3888
          ],
          "depot_type": 131,
          "owner": 4,
          "top_left_tile": [
            24,
            120
          ]
        },
        "mineral_indices": [
          394,
          386,
          356,
          369
        ],
        "gas_indices": [
          419
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 3
        },
        "parent_site_index": 6,
        "group_index": 0,
        "group_sizes": [
          4
        ],
        "source_anchor": [
          832,
          3888
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              3840,
              1392
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              118,
              42
            ]
          }
        ],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            3840,
            1392
          ],
          "depot_type": 154,
          "owner": null,
          "top_left_tile": [
            118,
            42
          ]
        },
        "mineral_indices": [
          101,
          103,
          98
        ],
        "gas_indices": [
          100
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 1
        },
        "parent_site_index": 7,
        "group_index": 0,
        "group_sizes": [
          3
        ],
        "source_anchor": [
          3840,
          1392
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              3840,
              1392
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              118,
              42
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      }
    ]
  },
  "407": {
    "input_unit_sha256": "483f2f5a4da61af74bd605844aeb8c7b9fa3bd9dc332c82a316e98b662a50e8c",
    "moves": [
      {
        "index": 16,
        "before": [
          1760,
          304,
          178,
          11
        ],
        "after": [
          1568,
          336,
          178,
          11
        ]
      },
      {
        "index": 17,
        "before": [
          1664,
          336,
          177,
          11
        ],
        "after": [
          1536,
          400,
          177,
          11
        ]
      },
      {
        "index": 20,
        "before": [
          1568,
          496,
          178,
          11
        ],
        "after": [
          1440,
          496,
          178,
          11
        ]
      },
      {
        "index": 21,
        "before": [
          1568,
          368,
          178,
          11
        ],
        "after": [
          1504,
          432,
          178,
          11
        ]
      },
      {
        "index": 22,
        "before": [
          2304,
          560,
          177,
          11
        ],
        "after": [
          1728,
          304,
          177,
          11
        ]
      },
      {
        "index": 25,
        "before": [
          1568,
          400,
          177,
          11
        ],
        "after": [
          1440,
          464,
          177,
          11
        ]
      },
      {
        "index": 26,
        "before": [
          1600,
          336,
          177,
          11
        ],
        "after": [
          1536,
          368,
          177,
          11
        ]
      },
      {
        "index": 30,
        "before": [
          2272,
          496,
          177,
          11
        ],
        "after": [
          1664,
          272,
          177,
          11
        ]
      },
      {
        "index": 37,
        "before": [
          2272,
          624,
          178,
          11
        ],
        "after": [
          1504,
          528,
          178,
          11
        ]
      },
      {
        "index": 41,
        "before": [
          2272,
          656,
          178,
          11
        ],
        "after": [
          1504,
          560,
          178,
          11
        ]
      },
      {
        "index": 42,
        "before": [
          2208,
          720,
          178,
          11
        ],
        "after": [
          1600,
          720,
          178,
          11
        ]
      },
      {
        "index": 43,
        "before": [
          2272,
          592,
          177,
          11
        ],
        "after": [
          1600,
          304,
          177,
          11
        ]
      },
      {
        "index": 48,
        "before": [
          2144,
          720,
          177,
          11
        ],
        "after": [
          1504,
          656,
          177,
          11
        ]
      },
      {
        "index": 75,
        "before": [
          1760,
          704,
          157,
          5
        ],
        "after": [
          1984,
          576,
          157,
          5
        ]
      },
      {
        "index": 292,
        "before": [
          1312,
          3568,
          177,
          11
        ],
        "after": [
          1312,
          3664,
          177,
          11
        ]
      },
      {
        "index": 293,
        "before": [
          1248,
          3120,
          176,
          11
        ],
        "after": [
          1248,
          3440,
          176,
          11
        ]
      },
      {
        "index": 297,
        "before": [
          1184,
          3120,
          178,
          11
        ],
        "after": [
          1184,
          3440,
          178,
          11
        ]
      },
      {
        "index": 299,
        "before": [
          1248,
          3440,
          177,
          11
        ],
        "after": [
          1312,
          3600,
          177,
          11
        ]
      },
      {
        "index": 300,
        "before": [
          1120,
          3120,
          176,
          11
        ],
        "after": [
          1120,
          3440,
          176,
          11
        ]
      },
      {
        "index": 301,
        "before": [
          1312,
          3536,
          178,
          11
        ],
        "after": [
          1312,
          3632,
          178,
          11
        ]
      },
      {
        "index": 306,
        "before": [
          1312,
          3600,
          177,
          11
        ],
        "after": [
          1248,
          3760,
          177,
          11
        ]
      },
      {
        "index": 309,
        "before": [
          1120,
          3440,
          177,
          11
        ],
        "after": [
          1120,
          3760,
          177,
          11
        ]
      },
      {
        "index": 313,
        "before": [
          1056,
          3440,
          176,
          11
        ],
        "after": [
          1056,
          3760,
          176,
          11
        ]
      },
      {
        "index": 315,
        "before": [
          1056,
          3120,
          177,
          11
        ],
        "after": [
          1056,
          3440,
          177,
          11
        ]
      },
      {
        "index": 316,
        "before": [
          1312,
          3184,
          178,
          11
        ],
        "after": [
          1312,
          3472,
          178,
          11
        ]
      },
      {
        "index": 317,
        "before": [
          1184,
          3440,
          177,
          11
        ],
        "after": [
          1184,
          3760,
          177,
          11
        ]
      },
      {
        "index": 318,
        "before": [
          1312,
          3280,
          178,
          11
        ],
        "after": [
          1312,
          3568,
          178,
          11
        ]
      },
      {
        "index": 323,
        "before": [
          1312,
          3216,
          176,
          11
        ],
        "after": [
          1312,
          3504,
          176,
          11
        ]
      },
      {
        "index": 324,
        "before": [
          1312,
          3248,
          176,
          11
        ],
        "after": [
          1312,
          3536,
          176,
          11
        ]
      },
      {
        "index": 328,
        "before": [
          3648,
          3696,
          176,
          11
        ],
        "after": [
          3552,
          4016,
          176,
          11
        ]
      },
      {
        "index": 329,
        "before": [
          3456,
          3376,
          177,
          11
        ],
        "after": [
          3328,
          3760,
          177,
          11
        ]
      },
      {
        "index": 331,
        "before": [
          3712,
          3728,
          177,
          11
        ],
        "after": [
          3680,
          4016,
          177,
          11
        ]
      },
      {
        "index": 332,
        "before": [
          1120,
          3776,
          188,
          11
        ],
        "after": [
          896,
          3584,
          188,
          11
        ]
      },
      {
        "index": 336,
        "before": [
          3520,
          3376,
          176,
          11
        ],
        "after": [
          3328,
          3792,
          176,
          11
        ]
      },
      {
        "index": 339,
        "before": [
          3584,
          3408,
          177,
          11
        ],
        "after": [
          3328,
          3888,
          177,
          11
        ]
      },
      {
        "index": 340,
        "before": [
          3584,
          3440,
          178,
          11
        ],
        "after": [
          3328,
          3920,
          178,
          11
        ]
      },
      {
        "index": 343,
        "before": [
          3584,
          4032,
          157,
          1
        ],
        "after": [
          3808,
          3840,
          157,
          1
        ]
      },
      {
        "index": 344,
        "before": [
          3712,
          3760,
          177,
          11
        ],
        "after": [
          3616,
          4016,
          177,
          11
        ]
      },
      {
        "index": 347,
        "before": [
          3456,
          3696,
          177,
          11
        ],
        "after": [
          3360,
          4016,
          177,
          11
        ]
      },
      {
        "index": 348,
        "before": [
          3584,
          3696,
          178,
          11
        ],
        "after": [
          3488,
          4016,
          178,
          11
        ]
      },
      {
        "index": 350,
        "before": [
          3520,
          3696,
          177,
          11
        ],
        "after": [
          3424,
          4016,
          177,
          11
        ]
      },
      {
        "index": 351,
        "before": [
          3392,
          3376,
          178,
          11
        ],
        "after": [
          3328,
          3856,
          178,
          11
        ]
      },
      {
        "index": 352,
        "before": [
          3584,
          3472,
          177,
          11
        ],
        "after": [
          3328,
          3952,
          177,
          11
        ]
      },
      {
        "index": 353,
        "before": [
          3328,
          3376,
          178,
          11
        ],
        "after": [
          3328,
          3824,
          178,
          11
        ]
      },
      {
        "index": 374,
        "before": [
          3776,
          3872,
          188,
          11
        ],
        "after": [
          3808,
          3904,
          188,
          11
        ]
      }
    ],
    "groups": [
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 188,
          "center": [
            320,
            1424
          ],
          "depot_type": 154,
          "owner": 5,
          "top_left_tile": [
            8,
            43
          ]
        },
        "mineral_indices": [
          159,
          186,
          189,
          166,
          184,
          190,
          195,
          181
        ],
        "gas_indices": [
          212
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 7,
          "geometry": 2,
          "army_route": 1
        },
        "parent_site_index": 0,
        "group_index": 0,
        "group_sizes": [
          8,
          8
        ],
        "source_anchor": [
          320,
          1424
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              960,
              1488
            ],
            "depot_type": 154,
            "owner": 5,
            "top_left_tile": [
              28,
              45
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1120,
              3600
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              33,
              111
            ]
          },
          {
            "kind": "expansion",
            "center": [
              1664,
              2128
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              50,
              65
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3456,
              2448
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              106,
              75
            ]
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            960,
            1488
          ],
          "depot_type": 154,
          "owner": 5,
          "top_left_tile": [
            28,
            45
          ],
          "additional_group_depot": true
        },
        "mineral_indices": [
          187,
          199,
          165,
          172,
          202,
          203,
          197,
          193
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 28,
          "geometry": 4
        },
        "parent_site_index": 0,
        "group_index": 1,
        "group_sizes": [
          8,
          8
        ],
        "source_anchor": [
          320,
          1424
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              960,
              1488
            ],
            "depot_type": 154,
            "owner": 5,
            "top_left_tile": [
              28,
              45
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1120,
              3600
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              33,
              111
            ]
          },
          {
            "kind": "expansion",
            "center": [
              1664,
              2128
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              50,
              65
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3456,
              2448
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              106,
              75
            ]
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            1120,
            3600
          ],
          "depot_type": 154,
          "owner": null,
          "top_left_tile": [
            33,
            111
          ]
        },
        "mineral_indices": [
          309,
          313,
          317,
          292,
          301,
          306,
          299,
          293,
          297,
          300,
          316,
          323,
          324,
          315,
          318
        ],
        "gas_indices": [
          332
        ],
        "status": "ladder_separate_gas",
        "reasons": {},
        "parent_site_index": 1,
        "group_index": 0,
        "group_sizes": [
          15
        ],
        "source_anchor": [
          1120,
          3600
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              960,
              1488
            ],
            "depot_type": 154,
            "owner": 5,
            "top_left_tile": [
              28,
              45
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1120,
              3600
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              33,
              111
            ]
          },
          {
            "kind": "expansion",
            "center": [
              1664,
              2128
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              50,
              65
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3456,
              2448
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              106,
              75
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "maximum_minerals": 15,
        "placement_policy": "reviewed_playtest_layout"
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 58,
          "center": [
            1760,
            496
          ],
          "depot_type": 154,
          "owner": 5,
          "top_left_tile": [
            53,
            14
          ]
        },
        "mineral_indices": [
          17,
          21,
          16,
          20,
          26,
          25,
          22,
          42,
          43,
          48,
          37,
          41,
          30
        ],
        "gas_indices": [
          75
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 28
        },
        "parent_site_index": 2,
        "group_index": 0,
        "group_sizes": [
          13
        ],
        "source_anchor": [
          1760,
          496
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              960,
              1488
            ],
            "depot_type": 154,
            "owner": 5,
            "top_left_tile": [
              28,
              45
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1120,
              3600
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              33,
              111
            ]
          },
          {
            "kind": "expansion",
            "center": [
              1664,
              2128
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              50,
              65
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3456,
              2448
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              106,
              75
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "maximum_minerals": 13,
        "placement_policy": "reviewed_playtest_layout"
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 333,
          "center": [
            3520,
            3856
          ],
          "depot_type": 154,
          "owner": 1,
          "top_left_tile": [
            108,
            119
          ]
        },
        "mineral_indices": [
          348,
          331,
          347,
          350,
          328,
          344,
          329,
          336,
          353,
          351,
          352,
          339,
          340
        ],
        "gas_indices": [
          343,
          374
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "resource_overlap": 1,
          "gas_exit": 1
        },
        "parent_site_index": 3,
        "group_index": 0,
        "group_sizes": [
          13
        ],
        "source_anchor": [
          3520,
          3856
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              960,
              1488
            ],
            "depot_type": 154,
            "owner": 5,
            "top_left_tile": [
              28,
              45
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1120,
              3600
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              33,
              111
            ]
          },
          {
            "kind": "expansion",
            "center": [
              1664,
              2128
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              50,
              65
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3456,
              2448
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              106,
              75
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "maximum_minerals": 13,
        "placement_policy": "reviewed_playtest_layout"
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 138,
          "center": [
            3808,
            1040
          ],
          "depot_type": 154,
          "owner": 5,
          "top_left_tile": [
            117,
            31
          ]
        },
        "mineral_indices": [
          163,
          173,
          148,
          169,
          152,
          168,
          177,
          178,
          154,
          161,
          167,
          175
        ],
        "gas_indices": [
          162
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 58,
          "gas_exit": 1,
          "gas_inside_bank": 1
        },
        "parent_site_index": 4,
        "group_index": 0,
        "group_sizes": [
          12
        ],
        "source_anchor": [
          3808,
          1040
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              960,
              1488
            ],
            "depot_type": 154,
            "owner": 5,
            "top_left_tile": [
              28,
              45
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1120,
              3600
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              33,
              111
            ]
          },
          {
            "kind": "expansion",
            "center": [
              1664,
              2128
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              50,
              65
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3456,
              2448
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              106,
              75
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            1664,
            2128
          ],
          "depot_type": 154,
          "owner": null,
          "top_left_tile": [
            50,
            65
          ]
        },
        "mineral_indices": [
          252,
          237,
          249,
          243,
          230,
          236,
          247,
          254,
          231,
          258
        ],
        "gas_indices": [
          220
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 12,
          "geometry": 1
        },
        "parent_site_index": 5,
        "group_index": 0,
        "group_sizes": [
          10
        ],
        "source_anchor": [
          1664,
          2128
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              960,
              1488
            ],
            "depot_type": 154,
            "owner": 5,
            "top_left_tile": [
              28,
              45
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1120,
              3600
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              33,
              111
            ]
          },
          {
            "kind": "expansion",
            "center": [
              1664,
              2128
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              50,
              65
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3456,
              2448
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              106,
              75
            ]
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            3456,
            2448
          ],
          "depot_type": 154,
          "owner": null,
          "top_left_tile": [
            106,
            75
          ]
        },
        "mineral_indices": [
          274,
          272,
          273,
          277,
          279,
          280,
          276,
          278,
          269,
          275
        ],
        "gas_indices": [
          281
        ],
        "status": "ladder_separate_gas",
        "reasons": {},
        "parent_site_index": 6,
        "group_index": 0,
        "group_sizes": [
          10
        ],
        "source_anchor": [
          3456,
          2448
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              960,
              1488
            ],
            "depot_type": 154,
            "owner": 5,
            "top_left_tile": [
              28,
              45
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1120,
              3600
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              33,
              111
            ]
          },
          {
            "kind": "expansion",
            "center": [
              1664,
              2128
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              50,
              65
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3456,
              2448
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              106,
              75
            ]
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      }
    ]
  },
  "408": {
    "input_unit_sha256": "d357ab5dbf36629bec042a279f8e8d7715e932c378c5d867bfad7d0b9cdfccca",
    "moves": [
      {
        "index": 278,
        "before": [
          4160,
          2720,
          188,
          11
        ],
        "after": [
          3872,
          2496,
          188,
          11
        ]
      }
    ],
    "groups": [
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            4064,
            2320
          ],
          "depot_type": 154,
          "owner": null,
          "top_left_tile": [
            125,
            71
          ]
        },
        "mineral_indices": [
          243,
          252,
          242,
          250,
          240,
          236,
          237,
          249,
          213
        ],
        "gas_indices": [
          278
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 3,
          "geometry": 6,
          "depot_clearance": 22,
          "gas_exit": 1
        },
        "parent_site_index": 0,
        "group_index": 0,
        "group_sizes": [
          9,
          10,
          10
        ],
        "source_anchor": [
          4064,
          2320
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              4064,
              2320
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              125,
              71
            ]
          },
          {
            "kind": "expansion",
            "center": [
              4256,
              2064
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              131,
              63
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              4448,
              2384
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              137,
              73
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              5600,
              4240
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              173,
              131
            ]
          }
        ],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            4256,
            2064
          ],
          "depot_type": 154,
          "owner": null,
          "top_left_tile": [
            131,
            63
          ],
          "additional_group_depot": true
        },
        "mineral_indices": [
          248,
          241,
          239,
          232,
          223,
          219,
          226,
          205,
          207,
          211
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 4
        },
        "parent_site_index": 0,
        "group_index": 1,
        "group_sizes": [
          9,
          10,
          10
        ],
        "source_anchor": [
          4064,
          2320
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              4064,
              2320
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              125,
              71
            ]
          },
          {
            "kind": "expansion",
            "center": [
              4256,
              2064
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              131,
              63
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              4448,
              2384
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              137,
              73
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              5600,
              4240
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              173,
              131
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            4448,
            2384
          ],
          "depot_type": 154,
          "owner": null,
          "top_left_tile": [
            137,
            73
          ],
          "additional_group_depot": true
        },
        "mineral_indices": [
          254,
          256,
          253,
          218,
          220,
          210,
          215,
          227,
          216,
          212
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 1
        },
        "parent_site_index": 0,
        "group_index": 2,
        "group_sizes": [
          9,
          10,
          10
        ],
        "source_anchor": [
          4064,
          2320
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              4064,
              2320
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              125,
              71
            ]
          },
          {
            "kind": "expansion",
            "center": [
              4256,
              2064
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              131,
              63
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              4448,
              2384
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              137,
              73
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              5600,
              4240
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              173,
              131
            ]
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 279,
          "center": [
            448,
            2672
          ],
          "depot_type": 154,
          "owner": 1,
          "top_left_tile": [
            12,
            82
          ]
        },
        "mineral_indices": [
          295,
          287,
          294,
          293,
          284,
          291,
          281,
          282,
          296,
          290
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 14,
          "plateau": 6
        },
        "parent_site_index": 1,
        "group_index": 0,
        "group_sizes": [
          10
        ],
        "source_anchor": [
          448,
          2672
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              4064,
              2320
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              125,
              71
            ]
          },
          {
            "kind": "expansion",
            "center": [
              4256,
              2064
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              131,
              63
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              4448,
              2384
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              137,
              73
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              5600,
              4240
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              173,
              131
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 736,
          "center": [
            512,
            4912
          ],
          "depot_type": 132,
          "owner": 0,
          "top_left_tile": [
            14,
            152
          ]
        },
        "mineral_indices": [
          451,
          453,
          472,
          469,
          475,
          465,
          476,
          459,
          478
        ],
        "gas_indices": [
          438
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 36
        },
        "parent_site_index": 2,
        "group_index": 0,
        "group_sizes": [
          9
        ],
        "source_anchor": [
          512,
          4912
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              4064,
              2320
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              125,
              71
            ]
          },
          {
            "kind": "expansion",
            "center": [
              4256,
              2064
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              131,
              63
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              4448,
              2384
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              137,
              73
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              5600,
              4240
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              173,
              131
            ]
          }
        ],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 547,
          "center": [
            640,
            464
          ],
          "depot_type": 133,
          "owner": 5,
          "top_left_tile": [
            18,
            13
          ]
        },
        "mineral_indices": [
          16,
          6,
          10,
          4,
          7,
          8,
          5,
          12
        ],
        "gas_indices": [
          52
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 1
        },
        "parent_site_index": 3,
        "group_index": 0,
        "group_sizes": [
          8
        ],
        "source_anchor": [
          640,
          464
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              4064,
              2320
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              125,
              71
            ]
          },
          {
            "kind": "expansion",
            "center": [
              4256,
              2064
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              131,
              63
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              4448,
              2384
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              137,
              73
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              5600,
              4240
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              173,
              131
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 626,
          "center": [
            5440,
            1520
          ],
          "depot_type": 133,
          "owner": 4,
          "top_left_tile": [
            168,
            46
          ]
        },
        "mineral_indices": [
          141,
          143,
          148,
          140,
          136,
          149,
          142,
          150
        ],
        "gas_indices": [
          172
        ],
        "status": "ladder_separate_gas",
        "reasons": {},
        "parent_site_index": 4,
        "group_index": 0,
        "group_sizes": [
          8
        ],
        "source_anchor": [
          5440,
          1520
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              4064,
              2320
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              125,
              71
            ]
          },
          {
            "kind": "expansion",
            "center": [
              4256,
              2064
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              131,
              63
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              4448,
              2384
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              137,
              73
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              5600,
              4240
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              173,
              131
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            5600,
            4240
          ],
          "depot_type": 154,
          "owner": null,
          "top_left_tile": [
            173,
            131
          ]
        },
        "mineral_indices": [
          366,
          370,
          371,
          363,
          364,
          369,
          374,
          378
        ],
        "gas_indices": [
          362
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 1
        },
        "parent_site_index": 5,
        "group_index": 0,
        "group_sizes": [
          8
        ],
        "source_anchor": [
          5600,
          4240
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              4064,
              2320
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              125,
              71
            ]
          },
          {
            "kind": "expansion",
            "center": [
              4256,
              2064
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              131,
              63
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              4448,
              2384
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              137,
              73
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              5600,
              4240
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              173,
              131
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 594,
          "center": [
            2144,
            1200
          ],
          "depot_type": 133,
          "owner": 5,
          "top_left_tile": [
            65,
            36
          ]
        },
        "mineral_indices": [
          120,
          103,
          144,
          107,
          137,
          131,
          98
        ],
        "gas_indices": [
          81
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 28,
          "plateau": 4,
          "gas_lane": 5,
          "gas_exit": 3
        },
        "parent_site_index": 6,
        "group_index": 0,
        "group_sizes": [
          7
        ],
        "source_anchor": [
          2144,
          1200
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              4064,
              2320
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              125,
              71
            ]
          },
          {
            "kind": "expansion",
            "center": [
              4256,
              2064
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              131,
              63
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              4448,
              2384
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              137,
              73
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              5600,
              4240
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              173,
              131
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 692,
          "center": [
            4896,
            3184
          ],
          "depot_type": 133,
          "owner": 4,
          "top_left_tile": [
            151,
            98
          ]
        },
        "mineral_indices": [
          331,
          323,
          316,
          317,
          320,
          312,
          321
        ],
        "gas_indices": [
          350
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 9
        },
        "parent_site_index": 7,
        "group_index": 0,
        "group_sizes": [
          7
        ],
        "source_anchor": [
          4896,
          3184
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              4064,
              2320
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              125,
              71
            ]
          },
          {
            "kind": "expansion",
            "center": [
              4256,
              2064
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              131,
              63
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              4448,
              2384
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              137,
              73
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              5600,
              4240
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              173,
              131
            ]
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 512,
          "center": [
            2144,
            5840
          ],
          "depot_type": 154,
          "owner": 1,
          "top_left_tile": [
            65,
            181
          ]
        },
        "mineral_indices": [
          521,
          501,
          506,
          510,
          511,
          516,
          520,
          508,
          523,
          505,
          524
        ],
        "gas_indices": [
          522,
          817
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 56,
          "resource_overlap": 2
        },
        "parent_site_index": 8,
        "group_index": 0,
        "group_sizes": [
          11
        ],
        "source_anchor": [
          2144,
          5840
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              4064,
              2320
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              125,
              71
            ]
          },
          {
            "kind": "expansion",
            "center": [
              4256,
              2064
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              131,
              63
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              4448,
              2384
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              137,
              73
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              5600,
              4240
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              173,
              131
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 556,
          "center": [
            3936,
            624
          ],
          "depot_type": 133,
          "owner": 5,
          "top_left_tile": [
            121,
            18
          ]
        },
        "mineral_indices": [
          14,
          24,
          31,
          30,
          43,
          28,
          23,
          27
        ],
        "gas_indices": [
          75
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 8
        },
        "parent_site_index": 9,
        "group_index": 0,
        "group_sizes": [
          8
        ],
        "source_anchor": [
          3936,
          624
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              4064,
              2320
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              125,
              71
            ]
          },
          {
            "kind": "expansion",
            "center": [
              4256,
              2064
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              131,
              63
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              4448,
              2384
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              137,
              73
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              5600,
              4240
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              173,
              131
            ]
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 714,
          "center": [
            4000,
            4432
          ],
          "depot_type": 133,
          "owner": 0,
          "top_left_tile": [
            123,
            137
          ]
        },
        "mineral_indices": [
          379,
          380,
          387,
          381,
          388,
          384,
          389,
          386
        ],
        "gas_indices": [
          421
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 35,
          "army_route": 11,
          "gas_exit": 1
        },
        "parent_site_index": 10,
        "group_index": 0,
        "group_sizes": [
          8
        ],
        "source_anchor": [
          4000,
          4432
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              4064,
              2320
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              125,
              71
            ]
          },
          {
            "kind": "expansion",
            "center": [
              4256,
              2064
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              131,
              63
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              4448,
              2384
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              137,
              73
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              5600,
              4240
            ],
            "depot_type": 154,
            "owner": null,
            "top_left_tile": [
              173,
              131
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      }
    ]
  },
  "501": {
    "input_unit_sha256": "53b5e3a0dad31d63362c9a85919e6cf2053b4dc3c27d79ae553c56c83e064a4e",
    "moves": [
      {
        "index": 227,
        "before": [
          288,
          1936,
          176,
          11
        ],
        "after": [
          96,
          2064,
          176,
          11
        ]
      },
      {
        "index": 241,
        "before": [
          352,
          2064,
          178,
          11
        ],
        "after": [
          256,
          2128,
          178,
          11
        ]
      },
      {
        "index": 245,
        "before": [
          352,
          1968,
          177,
          11
        ],
        "after": [
          160,
          2064,
          177,
          11
        ]
      },
      {
        "index": 247,
        "before": [
          256,
          2128,
          176,
          11
        ],
        "after": [
          256,
          2160,
          176,
          11
        ]
      }
    ],
    "groups": [
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 51,
          "center": [
            480,
            592
          ],
          "depot_type": 106,
          "owner": 0,
          "top_left_tile": [
            13,
            17
          ]
        },
        "mineral_indices": [
          14,
          28,
          26,
          19,
          24,
          33,
          27,
          31,
          32,
          22,
          35
        ],
        "gas_indices": [
          68
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 39,
          "geometry": 17
        },
        "parent_site_index": 0,
        "group_index": 0,
        "group_sizes": [
          11
        ],
        "source_anchor": [
          480,
          592
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              64,
              2224
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              0,
              68
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 285,
          "center": [
            576,
            2704
          ],
          "depot_type": 106,
          "owner": 5,
          "top_left_tile": [
            16,
            83
          ]
        },
        "mineral_indices": [
          294,
          283,
          290,
          282,
          288,
          292,
          266,
          274
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 14,
          "plateau": 12
        },
        "parent_site_index": 1,
        "group_index": 0,
        "group_sizes": [
          8
        ],
        "source_anchor": [
          576,
          2704
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              64,
              2224
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              0,
              68
            ]
          }
        ],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 197,
          "center": [
            2624,
            1424
          ],
          "depot_type": 106,
          "owner": 1,
          "top_left_tile": [
            80,
            43
          ]
        },
        "mineral_indices": [
          208,
          200,
          209,
          192,
          186,
          196,
          179
        ],
        "gas_indices": [
          173
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 1
        },
        "parent_site_index": 2,
        "group_index": 0,
        "group_sizes": [
          7
        ],
        "source_anchor": [
          2624,
          1424
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              64,
              2224
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              0,
              68
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            64,
            2224
          ],
          "depot_type": 106,
          "owner": null,
          "top_left_tile": [
            0,
            68
          ]
        },
        "mineral_indices": [
          227,
          245,
          241,
          247
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 150
        },
        "parent_site_index": 3,
        "group_index": 0,
        "group_sizes": [
          4
        ],
        "source_anchor": [
          64,
          2128
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              64,
              2224
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              0,
              68
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "maximum_minerals": 12,
        "placement_policy": "reviewed_playtest_layout"
      }
    ]
  },
  "503": {
    "input_unit_sha256": "3eb2cca22c4f72047747fd5a6999304ea053e2c36b6ff19cd3d038f77c13b360",
    "moves": [
      {
        "index": 270,
        "before": [
          768,
          3568,
          177,
          11
        ],
        "after": [
          736,
          4016,
          177,
          11
        ]
      },
      {
        "index": 273,
        "before": [
          928,
          3472,
          177,
          11
        ],
        "after": [
          800,
          4016,
          177,
          11
        ]
      },
      {
        "index": 274,
        "before": [
          768,
          3536,
          177,
          11
        ],
        "after": [
          672,
          4016,
          177,
          11
        ]
      },
      {
        "index": 275,
        "before": [
          800,
          3472,
          177,
          11
        ],
        "after": [
          544,
          3920,
          177,
          11
        ]
      },
      {
        "index": 276,
        "before": [
          768,
          3600,
          176,
          11
        ],
        "after": [
          608,
          4016,
          176,
          11
        ]
      },
      {
        "index": 277,
        "before": [
          864,
          3472,
          178,
          11
        ],
        "after": [
          544,
          3888,
          178,
          11
        ]
      },
      {
        "index": 278,
        "before": [
          1184,
          3712,
          188,
          11
        ],
        "after": [
          960,
          3904,
          188,
          11
        ]
      }
    ],
    "groups": [
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 296,
          "center": [
            544,
            752
          ],
          "depot_type": 133,
          "owner": 0,
          "top_left_tile": [
            15,
            22
          ]
        },
        "mineral_indices": [
          80,
          62,
          65,
          58,
          66,
          84,
          71,
          76,
          81,
          85
        ],
        "gas_indices": [
          42
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 21,
          "geometry": 33
        },
        "parent_site_index": 0,
        "group_index": 0,
        "group_sizes": [
          10
        ],
        "source_anchor": [
          544,
          752
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              1792,
              2064
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              54,
              63
            ]
          },
          {
            "kind": "expansion",
            "center": [
              736,
              3856
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              21,
              119
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 338,
          "center": [
            256,
            2288
          ],
          "depot_type": 133,
          "owner": 3,
          "top_left_tile": [
            6,
            70
          ]
        },
        "mineral_indices": [
          140,
          135,
          145,
          134,
          150,
          136,
          144,
          139,
          151
        ],
        "gas_indices": [
          141
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 26,
          "plateau": 20
        },
        "parent_site_index": 1,
        "group_index": 0,
        "group_sizes": [
          9
        ],
        "source_anchor": [
          256,
          2288
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              1792,
              2064
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              54,
              63
            ]
          },
          {
            "kind": "expansion",
            "center": [
              736,
              3856
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              21,
              119
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 288,
          "center": [
            2720,
            464
          ],
          "depot_type": 133,
          "owner": 4,
          "top_left_tile": [
            83,
            13
          ]
        },
        "mineral_indices": [
          34,
          19,
          17,
          22,
          13,
          26,
          38,
          9
        ],
        "gas_indices": [
          5
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 9
        },
        "parent_site_index": 2,
        "group_index": 0,
        "group_sizes": [
          8
        ],
        "source_anchor": [
          2720,
          464
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              1792,
              2064
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              54,
              63
            ]
          },
          {
            "kind": "expansion",
            "center": [
              736,
              3856
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              21,
              119
            ]
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 353,
          "center": [
            2496,
            3216
          ],
          "depot_type": 133,
          "owner": 5,
          "top_left_tile": [
            76,
            99
          ]
        },
        "mineral_indices": [
          202,
          197,
          203,
          210,
          194,
          198,
          209,
          195
        ],
        "gas_indices": [
          199
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 2,
          "plateau": 1
        },
        "parent_site_index": 3,
        "group_index": 0,
        "group_sizes": [
          8
        ],
        "source_anchor": [
          2496,
          3216
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              1792,
              2064
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              54,
              63
            ]
          },
          {
            "kind": "expansion",
            "center": [
              736,
              3856
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              21,
              119
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 246,
          "center": [
            1376,
            3376
          ],
          "depot_type": 106,
          "owner": 1,
          "top_left_tile": [
            41,
            104
          ]
        },
        "mineral_indices": [
          251,
          248,
          256,
          258,
          262,
          265,
          263
        ],
        "gas_indices": [
          266
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 1
        },
        "parent_site_index": 4,
        "group_index": 0,
        "group_sizes": [
          7
        ],
        "source_anchor": [
          1376,
          3376
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              1792,
              2064
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              54,
              63
            ]
          },
          {
            "kind": "expansion",
            "center": [
              736,
              3856
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              21,
              119
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            1792,
            2064
          ],
          "depot_type": 106,
          "owner": null,
          "top_left_tile": [
            54,
            63
          ]
        },
        "mineral_indices": [
          133,
          129,
          138,
          148,
          143,
          149
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {},
        "parent_site_index": 5,
        "group_index": 0,
        "group_sizes": [
          6
        ],
        "source_anchor": [
          1792,
          2064
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              1792,
              2064
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              54,
              63
            ]
          },
          {
            "kind": "expansion",
            "center": [
              736,
              3856
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              21,
              119
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            736,
            3856
          ],
          "depot_type": 106,
          "owner": null,
          "top_left_tile": [
            21,
            119
          ]
        },
        "mineral_indices": [
          273,
          270,
          274,
          275,
          276,
          277
        ],
        "gas_indices": [
          278
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 15
        },
        "parent_site_index": 6,
        "group_index": 0,
        "group_sizes": [
          6
        ],
        "source_anchor": [
          960,
          3632
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              1792,
              2064
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              54,
              63
            ]
          },
          {
            "kind": "expansion",
            "center": [
              736,
              3856
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              21,
              119
            ]
          }
        ],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "maximum_minerals": 12,
        "placement_policy": "reviewed_playtest_layout"
      }
    ]
  },
  "504": {
    "input_unit_sha256": "88a9b799c1d4619ab89392b894b3e7d5c31ee736e15e9a926a37f3039475b222",
    "moves": [
      {
        "index": 193,
        "before": [
          1760,
          1520,
          177,
          11
        ],
        "after": [
          1696,
          1808,
          177,
          11
        ]
      },
      {
        "index": 194,
        "before": [
          1504,
          2096,
          178,
          11
        ],
        "after": [
          1696,
          1968,
          178,
          11
        ]
      },
      {
        "index": 196,
        "before": [
          1440,
          2096,
          177,
          11
        ],
        "after": [
          1696,
          1936,
          177,
          11
        ]
      },
      {
        "index": 198,
        "before": [
          1312,
          1936,
          177,
          11
        ],
        "after": [
          1312,
          1840,
          177,
          11
        ]
      },
      {
        "index": 199,
        "before": [
          1696,
          1520,
          178,
          11
        ],
        "after": [
          1632,
          1776,
          178,
          11
        ]
      },
      {
        "index": 202,
        "before": [
          1312,
          1968,
          177,
          11
        ],
        "after": [
          1312,
          1872,
          177,
          11
        ]
      },
      {
        "index": 203,
        "before": [
          1584,
          1824,
          109,
          6
        ],
        "after": [
          1584,
          1664,
          109,
          6
        ]
      },
      {
        "index": 204,
        "before": [
          1376,
          2096,
          178,
          11
        ],
        "after": [
          1696,
          1904,
          178,
          11
        ]
      },
      {
        "index": 206,
        "before": [
          1680,
          1856,
          109,
          6
        ],
        "after": [
          1840,
          1792,
          109,
          6
        ]
      },
      {
        "index": 210,
        "before": [
          1568,
          1520,
          176,
          11
        ],
        "after": [
          1376,
          1776,
          176,
          11
        ]
      },
      {
        "index": 212,
        "before": [
          1504,
          1616,
          178,
          11
        ],
        "after": [
          1504,
          1776,
          178,
          11
        ]
      },
      {
        "index": 214,
        "before": [
          1632,
          1520,
          177,
          11
        ],
        "after": [
          1440,
          1776,
          177,
          11
        ]
      },
      {
        "index": 215,
        "before": [
          1312,
          2000,
          177,
          11
        ],
        "after": [
          1312,
          1904,
          177,
          11
        ]
      },
      {
        "index": 219,
        "before": [
          1312,
          2032,
          177,
          11
        ],
        "after": [
          1312,
          1936,
          177,
          11
        ]
      },
      {
        "index": 224,
        "before": [
          1504,
          1648,
          178,
          11
        ],
        "after": [
          1568,
          1776,
          178,
          11
        ]
      },
      {
        "index": 227,
        "before": [
          1504,
          1680,
          176,
          11
        ],
        "after": [
          1312,
          1808,
          176,
          11
        ]
      },
      {
        "index": 235,
        "before": [
          1472,
          1760,
          188,
          11
        ],
        "after": [
          1440,
          2112,
          188,
          11
        ]
      },
      {
        "index": 274,
        "before": [
          1120,
          2224,
          177,
          11
        ],
        "after": [
          704,
          2992,
          177,
          11
        ]
      },
      {
        "index": 275,
        "before": [
          736,
          2672,
          177,
          11
        ],
        "after": [
          416,
          3120,
          177,
          11
        ]
      },
      {
        "index": 276,
        "before": [
          864,
          2672,
          177,
          11
        ],
        "after": [
          512,
          3088,
          177,
          11
        ]
      },
      {
        "index": 277,
        "before": [
          608,
          2768,
          178,
          11
        ],
        "after": [
          320,
          3184,
          178,
          11
        ]
      },
      {
        "index": 278,
        "before": [
          672,
          2672,
          176,
          11
        ],
        "after": [
          448,
          3216,
          176,
          11
        ]
      },
      {
        "index": 279,
        "before": [
          992,
          2352,
          178,
          11
        ],
        "after": [
          576,
          3056,
          178,
          11
        ]
      },
      {
        "index": 280,
        "before": [
          1056,
          2224,
          178,
          11
        ],
        "after": [
          608,
          2960,
          178,
          11
        ]
      },
      {
        "index": 281,
        "before": [
          992,
          2320,
          176,
          11
        ],
        "after": [
          640,
          3024,
          176,
          11
        ]
      },
      {
        "index": 282,
        "before": [
          1184,
          2224,
          177,
          11
        ],
        "after": [
          608,
          2992,
          177,
          11
        ]
      },
      {
        "index": 287,
        "before": [
          992,
          2384,
          177,
          11
        ],
        "after": [
          448,
          3088,
          177,
          11
        ]
      },
      {
        "index": 288,
        "before": [
          608,
          2832,
          178,
          11
        ],
        "after": [
          352,
          3216,
          178,
          11
        ]
      },
      {
        "index": 291,
        "before": [
          800,
          2672,
          178,
          11
        ],
        "after": [
          416,
          3152,
          178,
          11
        ]
      },
      {
        "index": 295,
        "before": [
          1056,
          2816,
          110,
          1
        ],
        "after": [
          800,
          2656,
          110,
          1
        ]
      }
    ],
    "groups": [
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 216,
          "center": [
            1504,
            1936
          ],
          "depot_type": 106,
          "owner": 6,
          "top_left_tile": [
            45,
            59
          ]
        },
        "mineral_indices": [
          196,
          215,
          202,
          219,
          194,
          198,
          204,
          193,
          199,
          210,
          214,
          212,
          224,
          227
        ],
        "gas_indices": [
          235
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 8,
          "depot_clearance": 24
        },
        "parent_site_index": 0,
        "group_index": 0,
        "group_sizes": [
          14
        ],
        "source_anchor": [
          1504,
          1936
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              3072,
              2160
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              94,
              66
            ]
          },
          {
            "kind": "expansion",
            "center": [
              320,
              1808
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              8,
              55
            ]
          }
        ],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "maximum_minerals": 14,
        "placement_policy": "reviewed_playtest_layout"
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 292,
          "center": [
            800,
            2832
          ],
          "depot_type": 106,
          "owner": 1,
          "top_left_tile": [
            23,
            87
          ]
        },
        "mineral_indices": [
          275,
          291,
          277,
          278,
          288,
          276,
          274,
          280,
          282,
          281,
          279,
          287
        ],
        "gas_indices": [
          295
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 2,
          "geometry": 1
        },
        "parent_site_index": 1,
        "group_index": 0,
        "group_sizes": [
          12
        ],
        "source_anchor": [
          800,
          2832
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              3072,
              2160
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              94,
              66
            ]
          },
          {
            "kind": "expansion",
            "center": [
              320,
              1808
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              8,
              55
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "maximum_minerals": 12,
        "placement_policy": "reviewed_playtest_layout"
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 39,
          "center": [
            576,
            304
          ],
          "depot_type": 106,
          "owner": 0,
          "top_left_tile": [
            16,
            8
          ]
        },
        "mineral_indices": [
          9,
          24,
          6,
          15,
          23,
          7,
          10,
          1,
          16,
          8,
          2
        ],
        "gas_indices": [
          40
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 543,
          "geometry": 673
        },
        "parent_site_index": 2,
        "group_index": 0,
        "group_sizes": [
          11
        ],
        "source_anchor": [
          576,
          304
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              3072,
              2160
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              94,
              66
            ]
          },
          {
            "kind": "expansion",
            "center": [
              320,
              1808
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              8,
              55
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            3072,
            2160
          ],
          "depot_type": 106,
          "owner": null,
          "top_left_tile": [
            94,
            66
          ]
        },
        "mineral_indices": [
          252,
          267,
          266,
          257,
          262,
          258,
          250,
          261,
          264,
          255,
          256
        ],
        "gas_indices": [
          249
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 1193,
          "geometry": 23,
          "gas_lane": 36,
          "gas_inside_bank": 9
        },
        "parent_site_index": 3,
        "group_index": 0,
        "group_sizes": [
          11
        ],
        "source_anchor": [
          3072,
          2160
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              3072,
              2160
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              94,
              66
            ]
          },
          {
            "kind": "expansion",
            "center": [
              320,
              1808
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              8,
              55
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 123,
          "center": [
            3296,
            624
          ],
          "depot_type": 106,
          "owner": 0,
          "top_left_tile": [
            101,
            18
          ]
        },
        "mineral_indices": [
          78,
          83,
          96,
          95,
          100,
          84,
          103
        ],
        "gas_indices": [
          126
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 27,
          "gas_exit": 1
        },
        "parent_site_index": 4,
        "group_index": 0,
        "group_sizes": [
          7
        ],
        "source_anchor": [
          3296,
          624
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              3072,
              2160
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              94,
              66
            ]
          },
          {
            "kind": "expansion",
            "center": [
              320,
              1808
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              8,
              55
            ]
          }
        ],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 394,
          "center": [
            3648,
            3760
          ],
          "depot_type": 106,
          "owner": 1,
          "top_left_tile": [
            112,
            116
          ]
        },
        "mineral_indices": [
          421,
          405,
          415,
          430,
          406,
          416
        ],
        "gas_indices": [
          447
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 407,
          "plateau": 15
        },
        "parent_site_index": 5,
        "group_index": 0,
        "group_sizes": [
          6
        ],
        "source_anchor": [
          3648,
          3760
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              3072,
              2160
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              94,
              66
            ]
          },
          {
            "kind": "expansion",
            "center": [
              320,
              1808
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              8,
              55
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            320,
            1808
          ],
          "depot_type": 106,
          "owner": null,
          "top_left_tile": [
            8,
            55
          ]
        },
        "mineral_indices": [
          197,
          191,
          195,
          200,
          189,
          201,
          190,
          205
        ],
        "gas_indices": [
          192
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 3
        },
        "parent_site_index": 6,
        "group_index": 0,
        "group_sizes": [
          8
        ],
        "source_anchor": [
          320,
          1808
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              3072,
              2160
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              94,
              66
            ]
          },
          {
            "kind": "expansion",
            "center": [
              320,
              1808
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              8,
              55
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      }
    ]
  },
  "505": {
    "input_unit_sha256": "d3dec9259736bf98d79caf94e53fdae457c21e023aa3eb996c5f7d71eafb8724",
    "moves": [
      {
        "index": 522,
        "before": [
          688,
          3520,
          123,
          6
        ],
        "after": [
          688,
          3360,
          123,
          6
        ]
      },
      {
        "index": 547,
        "before": [
          816,
          3648,
          125,
          6
        ],
        "after": [
          976,
          3520,
          125,
          6
        ]
      }
    ],
    "groups": [
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 546,
          "center": [
            640,
            3664
          ],
          "depot_type": 106,
          "owner": 6,
          "top_left_tile": [
            18,
            113
          ]
        },
        "mineral_indices": [
          576,
          540,
          565,
          549,
          612,
          587,
          610,
          652,
          588,
          625,
          637,
          636
        ],
        "gas_indices": [
          607,
          710
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 30,
          "geometry": 19,
          "resource_overlap": 521,
          "gas_lane": 258,
          "gas_exit": 74,
          "army_route": 112,
          "gas_inside_bank": 817
        },
        "parent_site_index": 0,
        "group_index": 0,
        "group_sizes": [
          12
        ],
        "source_anchor": [
          640,
          3664
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5920,
              3632
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              183,
              112
            ]
          },
          {
            "kind": "expansion",
            "center": [
              256,
              2064
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              6,
              63
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3072,
              2256
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              94,
              69
            ]
          },
          {
            "kind": "expansion",
            "center": [
              256,
              112
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              6,
              2
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3840,
              3792
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              118,
              117
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            5920,
            3632
          ],
          "depot_type": 106,
          "owner": null,
          "top_left_tile": [
            183,
            112
          ]
        },
        "mineral_indices": [
          596,
          624,
          632,
          611,
          634,
          595,
          635,
          647,
          648,
          574,
          564,
          586
        ],
        "gas_indices": [
          649
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 35,
          "geometry": 23
        },
        "parent_site_index": 1,
        "group_index": 0,
        "group_sizes": [
          12
        ],
        "source_anchor": [
          5920,
          3632
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5920,
              3632
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              183,
              112
            ]
          },
          {
            "kind": "expansion",
            "center": [
              256,
              2064
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              6,
              63
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3072,
              2256
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              94,
              69
            ]
          },
          {
            "kind": "expansion",
            "center": [
              256,
              112
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              6,
              2
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3840,
              3792
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              118,
              117
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            256,
            2064
          ],
          "depot_type": 106,
          "owner": null,
          "top_left_tile": [
            6,
            63
          ]
        },
        "mineral_indices": [
          326,
          320,
          321,
          316,
          323,
          286,
          300,
          308,
          331,
          290,
          305
        ],
        "gas_indices": [
          328
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 47,
          "gas_lane": 2,
          "gas_exit": 2
        },
        "parent_site_index": 2,
        "group_index": 0,
        "group_sizes": [
          11
        ],
        "source_anchor": [
          256,
          2064
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5920,
              3632
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              183,
              112
            ]
          },
          {
            "kind": "expansion",
            "center": [
              256,
              2064
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              6,
              63
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3072,
              2256
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              94,
              69
            ]
          },
          {
            "kind": "expansion",
            "center": [
              256,
              112
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              6,
              2
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3840,
              3792
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              118,
              117
            ]
          }
        ],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 61,
          "center": [
            3552,
            272
          ],
          "depot_type": 106,
          "owner": 0,
          "top_left_tile": [
            109,
            7
          ]
        },
        "mineral_indices": [
          10,
          3,
          8,
          2,
          18,
          17,
          0,
          16,
          9
        ],
        "gas_indices": [
          38
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 21,
          "geometry": 25
        },
        "parent_site_index": 3,
        "group_index": 0,
        "group_sizes": [
          9
        ],
        "source_anchor": [
          3552,
          272
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5920,
              3632
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              183,
              112
            ]
          },
          {
            "kind": "expansion",
            "center": [
              256,
              2064
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              6,
              63
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3072,
              2256
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              94,
              69
            ]
          },
          {
            "kind": "expansion",
            "center": [
              256,
              112
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              6,
              2
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3840,
              3792
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              118,
              117
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            3072,
            2256
          ],
          "depot_type": 106,
          "owner": null,
          "top_left_tile": [
            94,
            69
          ]
        },
        "mineral_indices": [
          310,
          303,
          315,
          294,
          291,
          295,
          292,
          297,
          285
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 15,
          "geometry": 31
        },
        "parent_site_index": 4,
        "group_index": 0,
        "group_sizes": [
          9
        ],
        "source_anchor": [
          3072,
          2256
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5920,
              3632
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              183,
              112
            ]
          },
          {
            "kind": "expansion",
            "center": [
              256,
              2064
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              6,
              63
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3072,
              2256
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              94,
              69
            ]
          },
          {
            "kind": "expansion",
            "center": [
              256,
              112
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              6,
              2
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3840,
              3792
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              118,
              117
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            256,
            112
          ],
          "depot_type": 106,
          "owner": null,
          "top_left_tile": [
            6,
            2
          ]
        },
        "mineral_indices": [
          28,
          25,
          29,
          15,
          21,
          130,
          27,
          120,
          11,
          20,
          119
        ],
        "gas_indices": [
          100
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 56,
          "gas_inside_bank": 2,
          "gas_lane": 89,
          "gas_exit": 1
        },
        "parent_site_index": 5,
        "group_index": 0,
        "group_sizes": [
          11
        ],
        "source_anchor": [
          256,
          112
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5920,
              3632
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              183,
              112
            ]
          },
          {
            "kind": "expansion",
            "center": [
              256,
              2064
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              6,
              63
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3072,
              2256
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              94,
              69
            ]
          },
          {
            "kind": "expansion",
            "center": [
              256,
              112
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              6,
              2
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3840,
              3792
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              118,
              117
            ]
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 150,
          "center": [
            5120,
            624
          ],
          "depot_type": 106,
          "owner": 0,
          "top_left_tile": [
            158,
            18
          ]
        },
        "mineral_indices": [
          134,
          115,
          128,
          118,
          103,
          106,
          97,
          114
        ],
        "gas_indices": [
          152
        ],
        "status": "ladder_separate_gas",
        "reasons": {},
        "parent_site_index": 6,
        "group_index": 0,
        "group_sizes": [
          8
        ],
        "source_anchor": [
          5120,
          624
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5920,
              3632
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              183,
              112
            ]
          },
          {
            "kind": "expansion",
            "center": [
              256,
              2064
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              6,
              63
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3072,
              2256
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              94,
              69
            ]
          },
          {
            "kind": "expansion",
            "center": [
              256,
              112
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              6,
              2
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3840,
              3792
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              118,
              117
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 248,
          "center": [
            5728,
            1616
          ],
          "depot_type": 106,
          "owner": 1,
          "top_left_tile": [
            177,
            49
          ]
        },
        "mineral_indices": [
          224,
          231,
          227,
          228,
          222,
          225,
          226,
          223
        ],
        "gas_indices": [
          242
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 32,
          "plateau": 4
        },
        "parent_site_index": 7,
        "group_index": 0,
        "group_sizes": [
          8
        ],
        "source_anchor": [
          5728,
          1616
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5920,
              3632
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              183,
              112
            ]
          },
          {
            "kind": "expansion",
            "center": [
              256,
              2064
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              6,
              63
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3072,
              2256
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              94,
              69
            ]
          },
          {
            "kind": "expansion",
            "center": [
              256,
              112
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              6,
              2
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3840,
              3792
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              118,
              117
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 638,
          "center": [
            4576,
            3920
          ],
          "depot_type": 106,
          "owner": 0,
          "top_left_tile": [
            141,
            121
          ]
        },
        "mineral_indices": [
          622
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 1
        },
        "parent_site_index": 8,
        "group_index": 0,
        "group_sizes": [
          1
        ],
        "source_anchor": [
          4576,
          3920
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5920,
              3632
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              183,
              112
            ]
          },
          {
            "kind": "expansion",
            "center": [
              256,
              2064
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              6,
              63
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3072,
              2256
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              94,
              69
            ]
          },
          {
            "kind": "expansion",
            "center": [
              256,
              112
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              6,
              2
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3840,
              3792
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              118,
              117
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            3840,
            3792
          ],
          "depot_type": 106,
          "owner": null,
          "top_left_tile": [
            118,
            117
          ]
        },
        "mineral_indices": [
          665
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {},
        "parent_site_index": 9,
        "group_index": 0,
        "group_sizes": [
          1
        ],
        "source_anchor": [
          3840,
          3792
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5920,
              3632
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              183,
              112
            ]
          },
          {
            "kind": "expansion",
            "center": [
              256,
              2064
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              6,
              63
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3072,
              2256
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              94,
              69
            ]
          },
          {
            "kind": "expansion",
            "center": [
              256,
              112
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              6,
              2
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3840,
              3792
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              118,
              117
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      }
    ]
  },
  "506": {
    "input_unit_sha256": "38ae23b5ee249efbeb22060ffccabbb4017881f33078cefdca0f6405f0e55617",
    "moves": [
      {
        "index": 9,
        "before": [
          3776,
          144,
          176,
          11
        ],
        "after": [
          3520,
          496,
          176,
          11
        ]
      },
      {
        "index": 13,
        "before": [
          3872,
          208,
          177,
          11
        ],
        "after": [
          3648,
          528,
          177,
          11
        ]
      },
      {
        "index": 17,
        "before": [
          3872,
          176,
          178,
          11
        ],
        "after": [
          3584,
          528,
          178,
          11
        ]
      },
      {
        "index": 18,
        "before": [
          3872,
          272,
          178,
          11
        ],
        "after": [
          3776,
          528,
          178,
          11
        ]
      },
      {
        "index": 26,
        "before": [
          3840,
          144,
          177,
          11
        ],
        "after": [
          3552,
          112,
          177,
          11
        ]
      },
      {
        "index": 35,
        "before": [
          3264,
          400,
          176,
          11
        ],
        "after": [
          3456,
          496,
          176,
          11
        ]
      },
      {
        "index": 45,
        "before": [
          3424,
          368,
          177,
          11
        ],
        "after": [
          3424,
          336,
          177,
          11
        ]
      },
      {
        "index": 46,
        "before": [
          3424,
          336,
          177,
          11
        ],
        "after": [
          3488,
          176,
          177,
          11
        ]
      },
      {
        "index": 51,
        "before": [
          3328,
          400,
          178,
          11
        ],
        "after": [
          3456,
          400,
          178,
          11
        ]
      },
      {
        "index": 56,
        "before": [
          3872,
          240,
          176,
          11
        ],
        "after": [
          3712,
          528,
          176,
          11
        ]
      },
      {
        "index": 57,
        "before": [
          3392,
          400,
          178,
          11
        ],
        "after": [
          3424,
          368,
          178,
          11
        ]
      },
      {
        "index": 76,
        "before": [
          3648,
          480,
          157,
          1
        ],
        "after": [
          3904,
          288,
          157,
          1
        ]
      },
      {
        "index": 84,
        "before": [
          192,
          656,
          176,
          11
        ],
        "after": [
          192,
          624,
          176,
          11
        ]
      },
      {
        "index": 85,
        "before": [
          192,
          624,
          177,
          11
        ],
        "after": [
          192,
          592,
          177,
          11
        ]
      },
      {
        "index": 90,
        "before": [
          896,
          432,
          178,
          11
        ],
        "after": [
          384,
          464,
          178,
          11
        ]
      },
      {
        "index": 91,
        "before": [
          736,
          400,
          178,
          11
        ],
        "after": [
          192,
          496,
          178,
          11
        ]
      },
      {
        "index": 96,
        "before": [
          800,
          400,
          176,
          11
        ],
        "after": [
          192,
          528,
          176,
          11
        ]
      },
      {
        "index": 100,
        "before": [
          192,
          688,
          177,
          11
        ],
        "after": [
          192,
          656,
          177,
          11
        ]
      },
      {
        "index": 102,
        "before": [
          352,
          784,
          178,
          11
        ],
        "after": [
          192,
          688,
          178,
          11
        ]
      },
      {
        "index": 103,
        "before": [
          896,
          464,
          177,
          11
        ],
        "after": [
          256,
          464,
          177,
          11
        ]
      },
      {
        "index": 110,
        "before": [
          288,
          784,
          176,
          11
        ],
        "after": [
          192,
          720,
          176,
          11
        ]
      },
      {
        "index": 113,
        "before": [
          896,
          528,
          177,
          11
        ],
        "after": [
          192,
          560,
          177,
          11
        ]
      },
      {
        "index": 117,
        "before": [
          224,
          784,
          178,
          11
        ],
        "after": [
          192,
          752,
          178,
          11
        ]
      },
      {
        "index": 118,
        "before": [
          896,
          496,
          177,
          11
        ],
        "after": [
          448,
          464,
          177,
          11
        ]
      },
      {
        "index": 125,
        "before": [
          896,
          560,
          177,
          11
        ],
        "after": [
          256,
          784,
          177,
          11
        ]
      },
      {
        "index": 140,
        "before": [
          416,
          448,
          149,
          5
        ],
        "after": [
          608,
          576,
          149,
          5
        ]
      },
      {
        "index": 254,
        "before": [
          128,
          2752,
          188,
          11
        ],
        "after": [
          96,
          2304,
          188,
          11
        ]
      },
      {
        "index": 255,
        "before": [
          64,
          2416,
          176,
          11
        ],
        "after": [
          64,
          2736,
          176,
          11
        ]
      },
      {
        "index": 256,
        "before": [
          192,
          2416,
          178,
          11
        ],
        "after": [
          192,
          2736,
          178,
          11
        ]
      },
      {
        "index": 258,
        "before": [
          32,
          2096,
          178,
          11
        ],
        "after": [
          192,
          2416,
          178,
          11
        ]
      },
      {
        "index": 259,
        "before": [
          288,
          2096,
          176,
          11
        ],
        "after": [
          320,
          2448,
          176,
          11
        ]
      },
      {
        "index": 260,
        "before": [
          128,
          2416,
          176,
          11
        ],
        "after": [
          128,
          2736,
          176,
          11
        ]
      },
      {
        "index": 262,
        "before": [
          224,
          2096,
          178,
          11
        ],
        "after": [
          320,
          2480,
          178,
          11
        ]
      },
      {
        "index": 267,
        "before": [
          160,
          2096,
          176,
          11
        ],
        "after": [
          320,
          2512,
          176,
          11
        ]
      },
      {
        "index": 269,
        "before": [
          256,
          2416,
          178,
          11
        ],
        "after": [
          320,
          2608,
          178,
          11
        ]
      },
      {
        "index": 270,
        "before": [
          320,
          2512,
          178,
          11
        ],
        "after": [
          320,
          2640,
          178,
          11
        ]
      },
      {
        "index": 278,
        "before": [
          320,
          2576,
          176,
          11
        ],
        "after": [
          256,
          2736,
          176,
          11
        ]
      },
      {
        "index": 279,
        "before": [
          320,
          2128,
          177,
          11
        ],
        "after": [
          320,
          2544,
          177,
          11
        ]
      },
      {
        "index": 281,
        "before": [
          320,
          2160,
          178,
          11
        ],
        "after": [
          320,
          2576,
          178,
          11
        ]
      },
      {
        "index": 284,
        "before": [
          96,
          2096,
          176,
          11
        ],
        "after": [
          256,
          2416,
          176,
          11
        ]
      },
      {
        "index": 376,
        "before": [
          1248,
          2928,
          178,
          11
        ],
        "after": [
          1120,
          3568,
          178,
          11
        ]
      },
      {
        "index": 382,
        "before": [
          1440,
          3024,
          178,
          11
        ],
        "after": [
          1312,
          3344,
          178,
          11
        ]
      },
      {
        "index": 383,
        "before": [
          1376,
          2928,
          178,
          11
        ],
        "after": [
          1248,
          3344,
          178,
          11
        ]
      },
      {
        "index": 384,
        "before": [
          1056,
          2960,
          177,
          11
        ],
        "after": [
          1120,
          3440,
          177,
          11
        ]
      },
      {
        "index": 385,
        "before": [
          1056,
          2992,
          178,
          11
        ],
        "after": [
          1120,
          3472,
          178,
          11
        ]
      },
      {
        "index": 389,
        "before": [
          1440,
          2992,
          178,
          11
        ],
        "after": [
          1376,
          3344,
          178,
          11
        ]
      },
      {
        "index": 390,
        "before": [
          1440,
          2960,
          178,
          11
        ],
        "after": [
          1440,
          3344,
          178,
          11
        ]
      },
      {
        "index": 391,
        "before": [
          1120,
          2928,
          178,
          11
        ],
        "after": [
          1120,
          3504,
          178,
          11
        ]
      },
      {
        "index": 392,
        "before": [
          1184,
          2928,
          178,
          11
        ],
        "after": [
          1120,
          3536,
          178,
          11
        ]
      },
      {
        "index": 394,
        "before": [
          1312,
          2928,
          176,
          11
        ],
        "after": [
          1184,
          3344,
          176,
          11
        ]
      },
      {
        "index": 399,
        "before": [
          1312,
          3264,
          188,
          11
        ],
        "after": [
          1312,
          3680,
          188,
          11
        ]
      },
      {
        "index": 539,
        "before": [
          1152,
          3264,
          188,
          11
        ],
        "after": [
          1440,
          3680,
          188,
          11
        ]
      }
    ],
    "groups": [
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 37,
          "center": [
            3680,
            304
          ],
          "depot_type": 154,
          "owner": 1,
          "top_left_tile": [
            113,
            8
          ]
        },
        "mineral_indices": [
          9,
          18,
          13,
          56,
          17,
          26,
          35,
          51,
          45,
          57,
          36,
          25,
          46
        ],
        "gas_indices": [
          76
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "trigger_region": 96,
          "plateau": 8,
          "geometry": 8
        },
        "parent_site_index": 0,
        "group_index": 0,
        "group_sizes": [
          13
        ],
        "source_anchor": [
          3680,
          304
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              128,
              2576
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              2,
              79
            ]
          },
          {
            "kind": "expansion",
            "center": [
              1280,
              1968
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              38,
              60
            ]
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "maximum_minerals": 13,
        "placement_policy": "reviewed_playtest_layout"
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 451,
          "center": [
            384,
            624
          ],
          "depot_type": 133,
          "owner": 5,
          "top_left_tile": [
            10,
            18
          ]
        },
        "mineral_indices": [
          102,
          100,
          117,
          84,
          110,
          85,
          125,
          113,
          90,
          118,
          91,
          96,
          103
        ],
        "gas_indices": [
          140
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 14
        },
        "parent_site_index": 1,
        "group_index": 0,
        "group_sizes": [
          13
        ],
        "source_anchor": [
          384,
          624
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              128,
              2576
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              2,
              79
            ]
          },
          {
            "kind": "expansion",
            "center": [
              1280,
              1968
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              38,
              60
            ]
          }
        ],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "maximum_minerals": 13,
        "placement_policy": "reviewed_playtest_layout"
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            128,
            2576
          ],
          "depot_type": 106,
          "owner": null,
          "top_left_tile": [
            2,
            79
          ]
        },
        "mineral_indices": [
          260,
          255,
          256,
          270,
          269,
          278,
          258,
          259,
          262,
          267,
          284,
          279,
          281
        ],
        "gas_indices": [
          254
        ],
        "status": "ladder_separate_gas",
        "reasons": {},
        "parent_site_index": 2,
        "group_index": 0,
        "group_sizes": [
          13
        ],
        "source_anchor": [
          128,
          2576
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              128,
              2576
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              2,
              79
            ]
          },
          {
            "kind": "expansion",
            "center": [
              1280,
              1968
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              38,
              60
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "maximum_minerals": 13,
        "placement_policy": "reviewed_playtest_layout"
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 484,
          "center": [
            3616,
            3248
          ],
          "depot_type": 133,
          "owner": 4,
          "top_left_tile": [
            111,
            100
          ]
        },
        "mineral_indices": [
          403,
          406,
          408,
          400,
          402,
          395,
          407,
          401,
          410,
          413,
          409,
          411
        ],
        "gas_indices": [
          379
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 1,
          "gas_lane": 2
        },
        "parent_site_index": 3,
        "group_index": 0,
        "group_sizes": [
          12
        ],
        "source_anchor": [
          3616,
          3248
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              128,
              2576
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              2,
              79
            ]
          },
          {
            "kind": "expansion",
            "center": [
              1280,
              1968
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              38,
              60
            ]
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            1312,
            3504
          ],
          "depot_type": 106,
          "owner": 6,
          "top_left_tile": [
            39,
            108
          ],
          "scripted_starting_depot_location": 14
        },
        "mineral_indices": [
          382,
          390,
          391,
          376,
          383,
          389,
          384,
          392,
          385,
          394
        ],
        "gas_indices": [
          399,
          539
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 35,
          "resource_overlap": 1
        },
        "parent_site_index": 4,
        "group_index": 0,
        "group_sizes": [
          10
        ],
        "source_anchor": [
          1248,
          3088
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              128,
              2576
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              2,
              79
            ]
          },
          {
            "kind": "expansion",
            "center": [
              1280,
              1968
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              38,
              60
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "maximum_minerals": 12,
        "placement_policy": "reviewed_playtest_layout"
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            1280,
            1968
          ],
          "depot_type": 106,
          "owner": null,
          "top_left_tile": [
            38,
            60
          ]
        },
        "mineral_indices": [
          240,
          238,
          243,
          248,
          246,
          249,
          244,
          252,
          237
        ],
        "gas_indices": [
          235
        ],
        "status": "ladder_separate_gas",
        "reasons": {},
        "parent_site_index": 5,
        "group_index": 0,
        "group_sizes": [
          9
        ],
        "source_anchor": [
          1280,
          1968
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              128,
              2576
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              2,
              79
            ]
          },
          {
            "kind": "expansion",
            "center": [
              1280,
              1968
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              38,
              60
            ]
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      }
    ]
  },
  "508": {
    "input_unit_sha256": "c6ab4f207eb5dbcae71bc7a367e45ebbde7f5ed9d92b736d853714f626dc949b",
    "moves": [
      {
        "index": 47,
        "before": [
          1888,
          1776,
          176,
          11
        ],
        "after": [
          1760,
          1776,
          176,
          11
        ]
      },
      {
        "index": 48,
        "before": [
          1760,
          2224,
          177,
          11
        ],
        "after": [
          1568,
          1872,
          177,
          11
        ]
      },
      {
        "index": 51,
        "before": [
          1824,
          1776,
          177,
          11
        ],
        "after": [
          1696,
          1776,
          177,
          11
        ]
      },
      {
        "index": 52,
        "before": [
          1760,
          2320,
          178,
          11
        ],
        "after": [
          1568,
          1968,
          178,
          11
        ]
      },
      {
        "index": 54,
        "before": [
          1760,
          2192,
          176,
          11
        ],
        "after": [
          1568,
          1840,
          176,
          11
        ]
      },
      {
        "index": 55,
        "before": [
          1952,
          1840,
          178,
          11
        ],
        "after": [
          1824,
          1776,
          178,
          11
        ]
      },
      {
        "index": 60,
        "before": [
          1760,
          2256,
          178,
          11
        ],
        "after": [
          1568,
          1904,
          178,
          11
        ]
      },
      {
        "index": 61,
        "before": [
          1952,
          1808,
          178,
          11
        ],
        "after": [
          1888,
          1776,
          178,
          11
        ]
      },
      {
        "index": 62,
        "before": [
          1920,
          2352,
          178,
          11
        ],
        "after": [
          1952,
          1872,
          178,
          11
        ]
      },
      {
        "index": 65,
        "before": [
          1696,
          1776,
          177,
          11
        ],
        "after": [
          1568,
          1808,
          177,
          11
        ]
      },
      {
        "index": 75,
        "before": [
          1952,
          1872,
          176,
          11
        ],
        "after": [
          1952,
          1808,
          176,
          11
        ]
      },
      {
        "index": 85,
        "before": [
          1536,
          1920,
          149,
          0
        ],
        "after": [
          1760,
          2112,
          149,
          0
        ]
      },
      {
        "index": 86,
        "before": [
          1856,
          2352,
          178,
          11
        ],
        "after": [
          1952,
          1840,
          178,
          11
        ]
      },
      {
        "index": 91,
        "before": [
          1760,
          2288,
          177,
          11
        ],
        "after": [
          1568,
          1936,
          177,
          11
        ]
      },
      {
        "index": 104,
        "before": [
          1760,
          1776,
          178,
          11
        ],
        "after": [
          1632,
          1776,
          178,
          11
        ]
      },
      {
        "index": 107,
        "before": [
          1792,
          2352,
          177,
          11
        ],
        "after": [
          1568,
          2000,
          177,
          11
        ]
      },
      {
        "index": 192,
        "before": [
          3488,
          2784,
          149,
          4
        ],
        "after": [
          3264,
          2624,
          149,
          4
        ]
      },
      {
        "index": 197,
        "before": [
          2880,
          2672,
          177,
          11
        ],
        "after": [
          3264,
          2992,
          177,
          11
        ]
      },
      {
        "index": 198,
        "before": [
          2816,
          2672,
          178,
          11
        ],
        "after": [
          3072,
          2896,
          178,
          11
        ]
      },
      {
        "index": 202,
        "before": [
          3328,
          2992,
          178,
          11
        ],
        "after": [
          3456,
          2928,
          178,
          11
        ]
      },
      {
        "index": 203,
        "before": [
          3456,
          2896,
          177,
          11
        ],
        "after": [
          3456,
          2768,
          177,
          11
        ]
      },
      {
        "index": 207,
        "before": [
          3200,
          2992,
          176,
          11
        ],
        "after": [
          3328,
          2992,
          176,
          11
        ]
      },
      {
        "index": 223,
        "before": [
          2752,
          2768,
          176,
          11
        ],
        "after": [
          3072,
          2960,
          176,
          11
        ]
      },
      {
        "index": 224,
        "before": [
          3008,
          2672,
          178,
          11
        ],
        "after": [
          3456,
          2736,
          178,
          11
        ]
      },
      {
        "index": 225,
        "before": [
          3456,
          2928,
          177,
          11
        ],
        "after": [
          3456,
          2800,
          177,
          11
        ]
      },
      {
        "index": 226,
        "before": [
          3456,
          2960,
          177,
          11
        ],
        "after": [
          3456,
          2896,
          177,
          11
        ]
      },
      {
        "index": 232,
        "before": [
          2944,
          2672,
          176,
          11
        ],
        "after": [
          3456,
          2704,
          176,
          11
        ]
      },
      {
        "index": 233,
        "before": [
          3392,
          2992,
          177,
          11
        ],
        "after": [
          3456,
          2960,
          177,
          11
        ]
      },
      {
        "index": 234,
        "before": [
          2752,
          2832,
          177,
          11
        ],
        "after": [
          3136,
          2992,
          177,
          11
        ]
      },
      {
        "index": 235,
        "before": [
          2752,
          2736,
          178,
          11
        ],
        "after": [
          3072,
          2928,
          178,
          11
        ]
      },
      {
        "index": 239,
        "before": [
          2752,
          2800,
          178,
          11
        ],
        "after": [
          3200,
          2992,
          178,
          11
        ]
      },
      {
        "index": 240,
        "before": [
          3264,
          2992,
          178,
          11
        ],
        "after": [
          3392,
          2992,
          178,
          11
        ]
      }
    ],
    "groups": [
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 515,
          "center": [
            3680,
            1840
          ],
          "depot_type": 133,
          "owner": 4,
          "top_left_tile": [
            113,
            56
          ]
        },
        "mineral_indices": [
          81,
          80,
          89,
          70,
          88,
          49,
          68,
          99,
          58,
          69,
          98
        ],
        "gas_indices": [
          138
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 2
        },
        "parent_site_index": 0,
        "group_index": 0,
        "group_sizes": [
          11,
          11
        ],
        "source_anchor": [
          3680,
          1840
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              3680,
              2160
            ],
            "depot_type": 133,
            "owner": 4,
            "top_left_tile": [
              113,
              66
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              608,
              2224
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              17,
              68
            ]
          },
          {
            "kind": "expansion",
            "center": [
              608,
              2544
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              17,
              78
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              3168,
              5456
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              97,
              169
            ]
          }
        ],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            3680,
            2160
          ],
          "depot_type": 133,
          "owner": 4,
          "top_left_tile": [
            113,
            66
          ],
          "additional_group_depot": true
        },
        "mineral_indices": [
          111,
          100,
          56,
          50,
          57,
          41,
          40,
          35,
          31,
          34,
          21
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 31,
          "plateau": 25,
          "depot_clearance": 19
        },
        "parent_site_index": 0,
        "group_index": 1,
        "group_sizes": [
          11,
          11
        ],
        "source_anchor": [
          3680,
          1840
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              3680,
              2160
            ],
            "depot_type": 133,
            "owner": 4,
            "top_left_tile": [
              113,
              66
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              608,
              2224
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              17,
              68
            ]
          },
          {
            "kind": "expansion",
            "center": [
              608,
              2544
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              17,
              78
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              3168,
              5456
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              97,
              169
            ]
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            608,
            2224
          ],
          "depot_type": 106,
          "owner": null,
          "top_left_tile": [
            17,
            68
          ]
        },
        "mineral_indices": [
          113,
          108,
          116,
          146,
          131,
          139,
          123,
          133
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 5
        },
        "parent_site_index": 1,
        "group_index": 0,
        "group_sizes": [
          8,
          8
        ],
        "source_anchor": [
          608,
          2224
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              3680,
              2160
            ],
            "depot_type": 133,
            "owner": 4,
            "top_left_tile": [
              113,
              66
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              608,
              2224
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              17,
              68
            ]
          },
          {
            "kind": "expansion",
            "center": [
              608,
              2544
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              17,
              78
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              3168,
              5456
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              97,
              169
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            608,
            2544
          ],
          "depot_type": 106,
          "owner": null,
          "top_left_tile": [
            17,
            78
          ],
          "additional_group_depot": true
        },
        "mineral_indices": [
          128,
          122,
          125,
          92,
          132,
          124,
          115,
          129
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 11,
          "plateau": 19
        },
        "parent_site_index": 1,
        "group_index": 1,
        "group_sizes": [
          8,
          8
        ],
        "source_anchor": [
          608,
          2224
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              3680,
              2160
            ],
            "depot_type": 133,
            "owner": 4,
            "top_left_tile": [
              113,
              66
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              608,
              2224
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              17,
              68
            ]
          },
          {
            "kind": "expansion",
            "center": [
              608,
              2544
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              17,
              78
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              3168,
              5456
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              97,
              169
            ]
          }
        ],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 522,
          "center": [
            1760,
            1936
          ],
          "depot_type": 132,
          "owner": 0,
          "top_left_tile": [
            53,
            59
          ]
        },
        "mineral_indices": [
          55,
          51,
          61,
          47,
          65,
          75,
          104,
          107,
          86,
          62,
          52,
          91,
          60,
          48,
          54
        ],
        "gas_indices": [
          85
        ],
        "status": "ladder_separate_gas",
        "reasons": {},
        "parent_site_index": 2,
        "group_index": 0,
        "group_sizes": [
          15
        ],
        "source_anchor": [
          1760,
          1936
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              3680,
              2160
            ],
            "depot_type": 133,
            "owner": 4,
            "top_left_tile": [
              113,
              66
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              608,
              2224
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              17,
              68
            ]
          },
          {
            "kind": "expansion",
            "center": [
              608,
              2544
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              17,
              78
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              3168,
              5456
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              97,
              169
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "maximum_minerals": 15,
        "placement_policy": "reviewed_playtest_layout"
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 394,
          "center": [
            1440,
            5168
          ],
          "depot_type": 106,
          "owner": 6,
          "top_left_tile": [
            43,
            160
          ]
        },
        "mineral_indices": [
          426,
          429,
          405,
          406,
          410,
          399,
          417,
          401,
          425,
          398,
          421,
          397
        ],
        "gas_indices": [
          393,
          759
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 2,
          "resource_overlap": 4,
          "gas_inside_bank": 2,
          "gas_lane": 1
        },
        "parent_site_index": 3,
        "group_index": 0,
        "group_sizes": [
          12
        ],
        "source_anchor": [
          1440,
          5168
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              3680,
              2160
            ],
            "depot_type": 133,
            "owner": 4,
            "top_left_tile": [
              113,
              66
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              608,
              2224
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              17,
              68
            ]
          },
          {
            "kind": "expansion",
            "center": [
              608,
              2544
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              17,
              78
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              3168,
              5456
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              97,
              169
            ]
          }
        ],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            3168,
            5456
          ],
          "depot_type": 106,
          "owner": null,
          "top_left_tile": [
            97,
            169
          ]
        },
        "mineral_indices": [
          458,
          434,
          435,
          443,
          431,
          446,
          456,
          459,
          430,
          453,
          424,
          455
        ],
        "gas_indices": [
          460
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "sunken_range": 1,
          "gas_inside_bank": 6
        },
        "parent_site_index": 4,
        "group_index": 0,
        "group_sizes": [
          12
        ],
        "source_anchor": [
          3168,
          5456
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              3680,
              2160
            ],
            "depot_type": 133,
            "owner": 4,
            "top_left_tile": [
              113,
              66
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              608,
              2224
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              17,
              68
            ]
          },
          {
            "kind": "expansion",
            "center": [
              608,
              2544
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              17,
              78
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              3168,
              5456
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              97,
              169
            ]
          }
        ],
        "sunken_avoidance": {
          "hostile_owners": [
            0,
            4,
            5
          ],
          "unit_id": 146,
          "weapon_id": 53,
          "range_pixels": 224,
          "margin_pixels": 32,
          "worker_envelope_pixels": 32,
          "units_sha256": "da2ee6f116b77329048ec6be9e02721a527fde23d4b05b1b1336e634490abcba",
          "weapons_sha256": "80de165015519f9bed46ea8858195c2d2d0120b65b9e55e1c0a50b19135f4b62"
        },
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 619,
          "center": [
            4704,
            3504
          ],
          "depot_type": 133,
          "owner": 5,
          "top_left_tile": [
            145,
            108
          ]
        },
        "mineral_indices": [
          270,
          281,
          285,
          268,
          279,
          269,
          286,
          288,
          287,
          280,
          282
        ],
        "gas_indices": [
          307
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 3
        },
        "parent_site_index": 5,
        "group_index": 0,
        "group_sizes": [
          11
        ],
        "source_anchor": [
          4704,
          3504
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              3680,
              2160
            ],
            "depot_type": 133,
            "owner": 4,
            "top_left_tile": [
              113,
              66
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              608,
              2224
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              17,
              68
            ]
          },
          {
            "kind": "expansion",
            "center": [
              608,
              2544
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              17,
              78
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              3168,
              5456
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              97,
              169
            ]
          }
        ],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 693,
          "center": [
            5216,
            5616
          ],
          "depot_type": 133,
          "owner": 5,
          "top_left_tile": [
            161,
            174
          ]
        },
        "mineral_indices": [
          472,
          474,
          466,
          464,
          470,
          461,
          469,
          457
        ],
        "gas_indices": [
          471
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 1
        },
        "parent_site_index": 6,
        "group_index": 0,
        "group_sizes": [
          8
        ],
        "source_anchor": [
          5216,
          5616
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              3680,
              2160
            ],
            "depot_type": 133,
            "owner": 4,
            "top_left_tile": [
              113,
              66
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              608,
              2224
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              17,
              68
            ]
          },
          {
            "kind": "expansion",
            "center": [
              608,
              2544
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              17,
              78
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              3168,
              5456
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              97,
              169
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 597,
          "center": [
            1472,
            3152
          ],
          "depot_type": 131,
          "owner": 0,
          "top_left_tile": [
            44,
            97
          ]
        },
        "mineral_indices": [
          298,
          299,
          290,
          291,
          289,
          292,
          297
        ],
        "gas_indices": [
          247
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 8,
          "geometry": 24
        },
        "parent_site_index": 7,
        "group_index": 0,
        "group_sizes": [
          7
        ],
        "source_anchor": [
          1472,
          3152
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              3680,
              2160
            ],
            "depot_type": 133,
            "owner": 4,
            "top_left_tile": [
              113,
              66
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              608,
              2224
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              17,
              68
            ]
          },
          {
            "kind": "expansion",
            "center": [
              608,
              2544
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              17,
              78
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              3168,
              5456
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              97,
              169
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 575,
          "center": [
            3264,
            2832
          ],
          "depot_type": 132,
          "owner": 4,
          "top_left_tile": [
            100,
            87
          ]
        },
        "mineral_indices": [
          207,
          225,
          202,
          226,
          233,
          240,
          203,
          235,
          198,
          223,
          197,
          234,
          239,
          232,
          224
        ],
        "gas_indices": [
          192
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 1
        },
        "parent_site_index": 8,
        "group_index": 0,
        "group_sizes": [
          15
        ],
        "source_anchor": [
          3264,
          2832
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              3680,
              2160
            ],
            "depot_type": 133,
            "owner": 4,
            "top_left_tile": [
              113,
              66
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              608,
              2224
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              17,
              68
            ]
          },
          {
            "kind": "expansion",
            "center": [
              608,
              2544
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              17,
              78
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              3168,
              5456
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              97,
              169
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "maximum_minerals": 15,
        "placement_policy": "reviewed_playtest_layout"
      }
    ]
  },
  "515": {
    "input_unit_sha256": "2a51f1c2f3f1ff7287552f84173e0e5f8a1c387b82c3a035aafe4a6a19622c2c",
    "moves": [
      {
        "index": 11,
        "before": [
          384,
          272,
          177,
          11
        ],
        "after": [
          448,
          464,
          177,
          11
        ]
      },
      {
        "index": 12,
        "before": [
          512,
          112,
          178,
          11
        ],
        "after": [
          512,
          240,
          178,
          11
        ]
      },
      {
        "index": 13,
        "before": [
          128,
          432,
          177,
          11
        ],
        "after": [
          128,
          368,
          177,
          11
        ]
      },
      {
        "index": 16,
        "before": [
          128,
          400,
          178,
          11
        ],
        "after": [
          128,
          336,
          178,
          11
        ]
      },
      {
        "index": 17,
        "before": [
          512,
          144,
          177,
          11
        ],
        "after": [
          512,
          272,
          177,
          11
        ]
      },
      {
        "index": 23,
        "before": [
          128,
          464,
          177,
          11
        ],
        "after": [
          128,
          400,
          177,
          11
        ]
      },
      {
        "index": 24,
        "before": [
          224,
          592,
          178,
          11
        ],
        "after": [
          320,
          464,
          178,
          11
        ]
      },
      {
        "index": 26,
        "before": [
          512,
          208,
          177,
          11
        ],
        "after": [
          512,
          336,
          177,
          11
        ]
      },
      {
        "index": 27,
        "before": [
          512,
          176,
          178,
          11
        ],
        "after": [
          512,
          304,
          178,
          11
        ]
      },
      {
        "index": 28,
        "before": [
          128,
          528,
          177,
          11
        ],
        "after": [
          192,
          464,
          177,
          11
        ]
      },
      {
        "index": 89,
        "before": [
          96,
          96,
          188,
          11
        ],
        "after": [
          224,
          128,
          188,
          11
        ]
      },
      {
        "index": 109,
        "before": [
          160,
          592,
          178,
          11
        ],
        "after": [
          256,
          464,
          178,
          11
        ]
      },
      {
        "index": 118,
        "before": [
          128,
          496,
          176,
          11
        ],
        "after": [
          128,
          432,
          176,
          11
        ]
      },
      {
        "index": 119,
        "before": [
          320,
          272,
          177,
          11
        ],
        "after": [
          384,
          464,
          177,
          11
        ]
      },
      {
        "index": 127,
        "before": [
          448,
          272,
          178,
          11
        ],
        "after": [
          512,
          368,
          178,
          11
        ]
      }
    ],
    "groups": [
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            5952,
            3696
          ],
          "depot_type": 106,
          "owner": null,
          "top_left_tile": [
            184,
            114
          ]
        },
        "mineral_indices": [
          444,
          433,
          439,
          453,
          460,
          465,
          457,
          445,
          456,
          464,
          459,
          431
        ],
        "gas_indices": [
          463
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 42,
          "geometry": 16,
          "gas_exit": 4
        },
        "parent_site_index": 0,
        "group_index": 0,
        "group_sizes": [
          12
        ],
        "source_anchor": [
          5952,
          3696
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5952,
              3696
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              184,
              114
            ]
          },
          {
            "kind": "expansion",
            "center": [
              704,
              2096
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              20,
              64
            ]
          },
          {
            "kind": "expansion",
            "center": [
              320,
              304
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              8,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3072,
              2256
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              94,
              69
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3904,
              3664
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              120,
              113
            ]
          }
        ],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            704,
            2096
          ],
          "depot_type": 106,
          "owner": null,
          "top_left_tile": [
            20,
            64
          ]
        },
        "mineral_indices": [
          308,
          328,
          286,
          311,
          293,
          331,
          304,
          320,
          289,
          324,
          332
        ],
        "gas_indices": [
          327
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 1,
          "gas_exit": 1
        },
        "parent_site_index": 1,
        "group_index": 0,
        "group_sizes": [
          11
        ],
        "source_anchor": [
          704,
          2096
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5952,
              3696
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              184,
              114
            ]
          },
          {
            "kind": "expansion",
            "center": [
              704,
              2096
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              20,
              64
            ]
          },
          {
            "kind": "expansion",
            "center": [
              320,
              304
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              8,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3072,
              2256
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              94,
              69
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3904,
              3664
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              120,
              113
            ]
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 424,
          "center": [
            640,
            3664
          ],
          "depot_type": 106,
          "owner": 6,
          "top_left_tile": [
            18,
            113
          ]
        },
        "mineral_indices": [
          438,
          432,
          446,
          427,
          436,
          423,
          454,
          461,
          452,
          442,
          462
        ],
        "gas_indices": [
          447,
          524
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 4,
          "plateau": 2,
          "resource_overlap": 7,
          "gas_lane": 21
        },
        "parent_site_index": 2,
        "group_index": 0,
        "group_sizes": [
          11
        ],
        "source_anchor": [
          640,
          3664
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5952,
              3696
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              184,
              114
            ]
          },
          {
            "kind": "expansion",
            "center": [
              704,
              2096
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              20,
              64
            ]
          },
          {
            "kind": "expansion",
            "center": [
              320,
              304
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              8,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3072,
              2256
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              94,
              69
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3904,
              3664
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              120,
              113
            ]
          }
        ],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            320,
            304
          ],
          "depot_type": 106,
          "owner": null,
          "top_left_tile": [
            8,
            8
          ]
        },
        "mineral_indices": [
          27,
          26,
          119,
          11,
          17,
          12,
          127,
          118,
          28,
          109,
          24,
          23,
          13,
          16
        ],
        "gas_indices": [
          89
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 7,
          "geometry": 2
        },
        "parent_site_index": 3,
        "group_index": 0,
        "group_sizes": [
          14
        ],
        "source_anchor": [
          320,
          112
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5952,
              3696
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              184,
              114
            ]
          },
          {
            "kind": "expansion",
            "center": [
              704,
              2096
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              20,
              64
            ]
          },
          {
            "kind": "expansion",
            "center": [
              320,
              304
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              8,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3072,
              2256
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              94,
              69
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3904,
              3664
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              120,
              113
            ]
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "maximum_minerals": 14,
        "placement_policy": "reviewed_playtest_layout"
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 56,
          "center": [
            3552,
            272
          ],
          "depot_type": 106,
          "owner": 0,
          "top_left_tile": [
            109,
            7
          ]
        },
        "mineral_indices": [
          2,
          8,
          19,
          0,
          3,
          18,
          9,
          7,
          20
        ],
        "gas_indices": [
          36
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 21,
          "geometry": 25
        },
        "parent_site_index": 4,
        "group_index": 0,
        "group_sizes": [
          9
        ],
        "source_anchor": [
          3552,
          272
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5952,
              3696
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              184,
              114
            ]
          },
          {
            "kind": "expansion",
            "center": [
              704,
              2096
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              20,
              64
            ]
          },
          {
            "kind": "expansion",
            "center": [
              320,
              304
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              8,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3072,
              2256
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              94,
              69
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3904,
              3664
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              120,
              113
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            3072,
            2256
          ],
          "depot_type": 106,
          "owner": null,
          "top_left_tile": [
            94,
            69
          ]
        },
        "mineral_indices": [
          307,
          301,
          313,
          294,
          295,
          298,
          288,
          299,
          319
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 15,
          "geometry": 31
        },
        "parent_site_index": 5,
        "group_index": 0,
        "group_sizes": [
          9
        ],
        "source_anchor": [
          3072,
          2256
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5952,
              3696
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              184,
              114
            ]
          },
          {
            "kind": "expansion",
            "center": [
              704,
              2096
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              20,
              64
            ]
          },
          {
            "kind": "expansion",
            "center": [
              320,
              304
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              8,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3072,
              2256
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              94,
              69
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3904,
              3664
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              120,
              113
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 143,
          "center": [
            5120,
            624
          ],
          "depot_type": 106,
          "owner": 0,
          "top_left_tile": [
            158,
            18
          ]
        },
        "mineral_indices": [
          92,
          95,
          108,
          116,
          87,
          123,
          103,
          105
        ],
        "gas_indices": [
          145
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 36,
          "gas_exit": 3,
          "trigger_region": 12,
          "gas_lane": 3
        },
        "parent_site_index": 6,
        "group_index": 0,
        "group_sizes": [
          8
        ],
        "source_anchor": [
          5120,
          624
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5952,
              3696
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              184,
              114
            ]
          },
          {
            "kind": "expansion",
            "center": [
              704,
              2096
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              20,
              64
            ]
          },
          {
            "kind": "expansion",
            "center": [
              320,
              304
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              8,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3072,
              2256
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              94,
              69
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3904,
              3664
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              120,
              113
            ]
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 248,
          "center": [
            5728,
            1616
          ],
          "depot_type": 106,
          "owner": 1,
          "top_left_tile": [
            177,
            49
          ]
        },
        "mineral_indices": [
          222,
          229,
          225,
          226,
          220,
          223,
          224,
          221
        ],
        "gas_indices": [
          240
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 32,
          "plateau": 4
        },
        "parent_site_index": 7,
        "group_index": 0,
        "group_sizes": [
          8
        ],
        "source_anchor": [
          5728,
          1616
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5952,
              3696
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              184,
              114
            ]
          },
          {
            "kind": "expansion",
            "center": [
              704,
              2096
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              20,
              64
            ]
          },
          {
            "kind": "expansion",
            "center": [
              320,
              304
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              8,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3072,
              2256
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              94,
              69
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3904,
              3664
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              120,
              113
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            3904,
            3664
          ],
          "depot_type": 106,
          "owner": null,
          "top_left_tile": [
            120,
            113
          ]
        },
        "mineral_indices": [
          450,
          467
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {},
        "parent_site_index": 8,
        "group_index": 0,
        "group_sizes": [
          2
        ],
        "source_anchor": [
          3904,
          3664
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5952,
              3696
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              184,
              114
            ]
          },
          {
            "kind": "expansion",
            "center": [
              704,
              2096
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              20,
              64
            ]
          },
          {
            "kind": "expansion",
            "center": [
              320,
              304
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              8,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3072,
              2256
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              94,
              69
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3904,
              3664
            ],
            "depot_type": 106,
            "owner": null,
            "top_left_tile": [
              120,
              113
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      }
    ]
  },
  "602": {
    "input_unit_sha256": "64bbc02ce0360f87bc0518074445c73abc85fe2579a3b9aa76feab2b18d6fe97",
    "moves": [
      {
        "index": 23,
        "before": [
          2400,
          288,
          110,
          7
        ],
        "after": [
          2624,
          128,
          110,
          7
        ]
      },
      {
        "index": 196,
        "before": [
          512,
          2208,
          188,
          11
        ],
        "after": [
          480,
          2208,
          188,
          11
        ]
      },
      {
        "index": 247,
        "before": [
          1344,
          3584,
          188,
          11
        ],
        "after": [
          1664,
          3744,
          188,
          11
        ]
      }
    ],
    "groups": [
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 75,
          "center": [
            2624,
            304
          ],
          "depot_type": 106,
          "owner": 7,
          "top_left_tile": [
            80,
            8
          ]
        },
        "mineral_indices": [
          42,
          2,
          69,
          8,
          1,
          31,
          6,
          76,
          16,
          17,
          7,
          9
        ],
        "gas_indices": [
          23
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 34,
          "plateau": 24,
          "gas_inside_bank": 3,
          "gas_exit": 4,
          "gas_lane": 5
        },
        "parent_site_index": 0,
        "group_index": 0,
        "group_sizes": [
          12
        ],
        "source_anchor": [
          2624,
          304
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              3616,
              2512
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              111,
              77
            ]
          },
          {
            "kind": "expansion",
            "center": [
              1568,
              3568
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              47,
              110
            ]
          },
          {
            "kind": "expansion",
            "center": [
              352,
              176
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              9,
              4
            ]
          },
          {
            "kind": "expansion",
            "center": [
              480,
              2032
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              13,
              62
            ]
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 91,
          "center": [
            1536,
            368
          ],
          "depot_type": 106,
          "owner": 7,
          "top_left_tile": [
            46,
            10
          ]
        },
        "mineral_indices": [
          52,
          90,
          81,
          98,
          51,
          73,
          38,
          66,
          39
        ],
        "gas_indices": [
          29
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 33,
          "plateau": 13
        },
        "parent_site_index": 1,
        "group_index": 0,
        "group_sizes": [
          9
        ],
        "source_anchor": [
          1536,
          368
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              3616,
              2512
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              111,
              77
            ]
          },
          {
            "kind": "expansion",
            "center": [
              1568,
              3568
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              47,
              110
            ]
          },
          {
            "kind": "expansion",
            "center": [
              352,
              176
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              9,
              4
            ]
          },
          {
            "kind": "expansion",
            "center": [
              480,
              2032
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              13,
              62
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            3616,
            2512
          ],
          "depot_type": 131,
          "owner": null,
          "top_left_tile": [
            111,
            77
          ]
        },
        "mineral_indices": [
          198,
          197,
          204,
          212,
          208,
          214,
          203,
          216
        ],
        "gas_indices": [
          190
        ],
        "status": "ladder_separate_gas",
        "reasons": {},
        "parent_site_index": 2,
        "group_index": 0,
        "group_sizes": [
          8
        ],
        "source_anchor": [
          3616,
          2512
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              3616,
              2512
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              111,
              77
            ]
          },
          {
            "kind": "expansion",
            "center": [
              1568,
              3568
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              47,
              110
            ]
          },
          {
            "kind": "expansion",
            "center": [
              352,
              176
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              9,
              4
            ]
          },
          {
            "kind": "expansion",
            "center": [
              480,
              2032
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              13,
              62
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            1568,
            3568
          ],
          "depot_type": 131,
          "owner": null,
          "top_left_tile": [
            47,
            110
          ]
        },
        "mineral_indices": [
          250,
          249,
          251,
          256,
          254,
          257,
          252,
          259
        ],
        "gas_indices": [
          247
        ],
        "status": "ladder_separate_gas",
        "reasons": {},
        "parent_site_index": 3,
        "group_index": 0,
        "group_sizes": [
          8
        ],
        "source_anchor": [
          1568,
          3568
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              3616,
              2512
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              111,
              77
            ]
          },
          {
            "kind": "expansion",
            "center": [
              1568,
              3568
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              47,
              110
            ]
          },
          {
            "kind": "expansion",
            "center": [
              352,
              176
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              9,
              4
            ]
          },
          {
            "kind": "expansion",
            "center": [
              480,
              2032
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              13,
              62
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            352,
            176
          ],
          "depot_type": 131,
          "owner": null,
          "top_left_tile": [
            9,
            4
          ]
        },
        "mineral_indices": [
          37,
          0,
          50,
          79,
          71,
          80,
          72,
          89
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 3
        },
        "parent_site_index": 4,
        "group_index": 0,
        "group_sizes": [
          8
        ],
        "source_anchor": [
          352,
          176
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              3616,
              2512
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              111,
              77
            ]
          },
          {
            "kind": "expansion",
            "center": [
              1568,
              3568
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              47,
              110
            ]
          },
          {
            "kind": "expansion",
            "center": [
              352,
              176
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              9,
              4
            ]
          },
          {
            "kind": "expansion",
            "center": [
              480,
              2032
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              13,
              62
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            480,
            2032
          ],
          "depot_type": 131,
          "owner": null,
          "top_left_tile": [
            13,
            62
          ]
        },
        "mineral_indices": [
          177,
          176,
          178,
          180,
          179,
          187
        ],
        "gas_indices": [
          196
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 21,
          "geometry": 7,
          "army_route": 12
        },
        "parent_site_index": 5,
        "group_index": 0,
        "group_sizes": [
          6
        ],
        "source_anchor": [
          480,
          2032
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              3616,
              2512
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              111,
              77
            ]
          },
          {
            "kind": "expansion",
            "center": [
              1568,
              3568
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              47,
              110
            ]
          },
          {
            "kind": "expansion",
            "center": [
              352,
              176
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              9,
              4
            ]
          },
          {
            "kind": "expansion",
            "center": [
              480,
              2032
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              13,
              62
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      }
    ]
  },
  "603": {
    "input_unit_sha256": "78d08f54fac0f0603a867640f3dd102b2a44381a570bd6c71af181db19ca6354",
    "moves": [
      {
        "index": 0,
        "before": [
          3424,
          784,
          177,
          11
        ],
        "after": [
          3168,
          272,
          177,
          11
        ]
      },
      {
        "index": 1,
        "before": [
          3616,
          400,
          178,
          11
        ],
        "after": [
          3520,
          48,
          178,
          11
        ]
      },
      {
        "index": 2,
        "before": [
          3296,
          784,
          178,
          11
        ],
        "after": [
          3744,
          464,
          178,
          11
        ]
      },
      {
        "index": 3,
        "before": [
          3680,
          560,
          177,
          11
        ],
        "after": [
          3584,
          48,
          177,
          11
        ]
      },
      {
        "index": 4,
        "before": [
          3424,
          96,
          110,
          1
        ],
        "after": [
          3424,
          608,
          110,
          1
        ]
      },
      {
        "index": 6,
        "before": [
          3744,
          464,
          178,
          11
        ],
        "after": [
          3680,
          112,
          178,
          11
        ]
      },
      {
        "index": 8,
        "before": [
          3488,
          784,
          178,
          11
        ],
        "after": [
          3776,
          432,
          178,
          11
        ]
      },
      {
        "index": 10,
        "before": [
          3808,
          496,
          177,
          11
        ],
        "after": [
          3776,
          304,
          177,
          11
        ]
      },
      {
        "index": 12,
        "before": [
          3744,
          560,
          177,
          11
        ],
        "after": [
          3712,
          208,
          177,
          11
        ]
      },
      {
        "index": 13,
        "before": [
          3616,
          560,
          178,
          11
        ],
        "after": [
          3392,
          80,
          178,
          11
        ]
      },
      {
        "index": 18,
        "before": [
          3232,
          656,
          178,
          11
        ],
        "after": [
          3168,
          144,
          178,
          11
        ]
      },
      {
        "index": 20,
        "before": [
          3232,
          720,
          177,
          11
        ],
        "after": [
          3104,
          240,
          177,
          11
        ]
      },
      {
        "index": 21,
        "before": [
          3360,
          784,
          178,
          11
        ],
        "after": [
          3776,
          400,
          178,
          11
        ]
      },
      {
        "index": 25,
        "before": [
          3232,
          688,
          178,
          11
        ],
        "after": [
          3136,
          176,
          178,
          11
        ]
      },
      {
        "index": 32,
        "before": [
          3616,
          432,
          178,
          11
        ],
        "after": [
          3456,
          80,
          178,
          11
        ]
      },
      {
        "index": 39,
        "before": [
          3232,
          624,
          177,
          11
        ],
        "after": [
          3296,
          144,
          177,
          11
        ]
      },
      {
        "index": 50,
        "before": [
          288,
          1104,
          177,
          11
        ],
        "after": [
          736,
          560,
          177,
          11
        ]
      },
      {
        "index": 51,
        "before": [
          416,
          1104,
          177,
          11
        ],
        "after": [
          768,
          656,
          177,
          11
        ]
      },
      {
        "index": 53,
        "before": [
          256,
          1136,
          176,
          11
        ],
        "after": [
          736,
          592,
          176,
          11
        ]
      },
      {
        "index": 54,
        "before": [
          448,
          400,
          177,
          11
        ],
        "after": [
          704,
          432,
          177,
          11
        ]
      },
      {
        "index": 67,
        "before": [
          256,
          1200,
          177,
          11
        ],
        "after": [
          672,
          720,
          177,
          11
        ]
      },
      {
        "index": 72,
        "before": [
          384,
          400,
          177,
          11
        ],
        "after": [
          672,
          400,
          177,
          11
        ]
      },
      {
        "index": 73,
        "before": [
          256,
          1232,
          178,
          11
        ],
        "after": [
          640,
          752,
          178,
          11
        ]
      },
      {
        "index": 74,
        "before": [
          256,
          1168,
          177,
          11
        ],
        "after": [
          736,
          624,
          177,
          11
        ]
      },
      {
        "index": 75,
        "before": [
          320,
          400,
          178,
          11
        ],
        "after": [
          672,
          368,
          178,
          11
        ]
      },
      {
        "index": 83,
        "before": [
          224,
          1264,
          177,
          11
        ],
        "after": [
          576,
          752,
          177,
          11
        ]
      },
      {
        "index": 84,
        "before": [
          672,
          416,
          110,
          6
        ],
        "after": [
          384,
          384,
          110,
          6
        ]
      },
      {
        "index": 92,
        "before": [
          224,
          1296,
          177,
          11
        ],
        "after": [
          512,
          752,
          177,
          11
        ]
      },
      {
        "index": 93,
        "before": [
          256,
          464,
          176,
          11
        ],
        "after": [
          608,
          336,
          176,
          11
        ]
      },
      {
        "index": 105,
        "before": [
          256,
          496,
          177,
          11
        ],
        "after": [
          704,
          464,
          177,
          11
        ]
      },
      {
        "index": 115,
        "before": [
          256,
          528,
          177,
          11
        ],
        "after": [
          704,
          496,
          177,
          11
        ]
      },
      {
        "index": 120,
        "before": [
          256,
          560,
          177,
          11
        ],
        "after": [
          704,
          528,
          177,
          11
        ]
      },
      {
        "index": 165,
        "before": [
          1856,
          1472,
          110,
          4
        ],
        "after": [
          1824,
          1408,
          110,
          4
        ]
      },
      {
        "index": 174,
        "before": [
          1632,
          1008,
          178,
          11
        ],
        "after": [
          1600,
          1008,
          178,
          11
        ]
      },
      {
        "index": 177,
        "before": [
          1792,
          880,
          176,
          11
        ],
        "after": [
          1760,
          848,
          176,
          11
        ]
      },
      {
        "index": 178,
        "before": [
          1632,
          1040,
          177,
          11
        ],
        "after": [
          1568,
          1040,
          177,
          11
        ]
      },
      {
        "index": 179,
        "before": [
          1632,
          1104,
          177,
          11
        ],
        "after": [
          1536,
          1104,
          177,
          11
        ]
      },
      {
        "index": 184,
        "before": [
          1856,
          944,
          178,
          11
        ],
        "after": [
          1824,
          816,
          178,
          11
        ]
      },
      {
        "index": 185,
        "before": [
          1632,
          1072,
          177,
          11
        ],
        "after": [
          1440,
          1072,
          177,
          11
        ]
      },
      {
        "index": 192,
        "before": [
          1728,
          944,
          178,
          11
        ],
        "after": [
          1696,
          944,
          178,
          11
        ]
      },
      {
        "index": 197,
        "before": [
          1632,
          1136,
          177,
          11
        ],
        "after": [
          1536,
          1136,
          177,
          11
        ]
      },
      {
        "index": 200,
        "before": [
          3744,
          1424,
          178,
          11
        ],
        "after": [
          3840,
          1328,
          178,
          11
        ]
      },
      {
        "index": 203,
        "before": [
          3680,
          1456,
          177,
          11
        ],
        "after": [
          3776,
          1424,
          177,
          11
        ]
      },
      {
        "index": 205,
        "before": [
          3616,
          1424,
          176,
          11
        ],
        "after": [
          3712,
          1424,
          176,
          11
        ]
      },
      {
        "index": 293,
        "before": [
          1120,
          2256,
          178,
          11
        ],
        "after": [
          1760,
          2448,
          178,
          11
        ]
      },
      {
        "index": 295,
        "before": [
          704,
          2160,
          177,
          11
        ],
        "after": [
          896,
          2160,
          177,
          11
        ]
      },
      {
        "index": 296,
        "before": [
          640,
          2160,
          178,
          11
        ],
        "after": [
          704,
          2160,
          178,
          11
        ]
      },
      {
        "index": 300,
        "before": [
          1248,
          2320,
          177,
          11
        ],
        "after": [
          1760,
          2384,
          177,
          11
        ]
      },
      {
        "index": 301,
        "before": [
          1248,
          2288,
          177,
          11
        ],
        "after": [
          1760,
          2352,
          177,
          11
        ]
      },
      {
        "index": 302,
        "before": [
          864,
          3152,
          177,
          11
        ],
        "after": [
          1728,
          2544,
          177,
          11
        ]
      },
      {
        "index": 303,
        "before": [
          992,
          2160,
          178,
          11
        ],
        "after": [
          1728,
          2288,
          178,
          11
        ]
      },
      {
        "index": 314,
        "before": [
          2816,
          2544,
          176,
          11
        ],
        "after": [
          2944,
          2416,
          176,
          11
        ]
      },
      {
        "index": 315,
        "before": [
          768,
          2048,
          110,
          5
        ],
        "after": [
          576,
          2368,
          110,
          5
        ]
      },
      {
        "index": 318,
        "before": [
          2816,
          2576,
          176,
          11
        ],
        "after": [
          2816,
          2512,
          176,
          11
        ]
      },
      {
        "index": 321,
        "before": [
          2816,
          2608,
          178,
          11
        ],
        "after": [
          2816,
          2544,
          178,
          11
        ]
      },
      {
        "index": 325,
        "before": [
          2816,
          2640,
          178,
          11
        ],
        "after": [
          2816,
          2576,
          178,
          11
        ]
      },
      {
        "index": 327,
        "before": [
          2816,
          2512,
          177,
          11
        ],
        "after": [
          2880,
          2416,
          177,
          11
        ]
      },
      {
        "index": 336,
        "before": [
          2112,
          2544,
          176,
          11
        ],
        "after": [
          2080,
          2544,
          176,
          11
        ]
      },
      {
        "index": 338,
        "before": [
          2112,
          2640,
          177,
          11
        ],
        "after": [
          2080,
          2672,
          177,
          11
        ]
      },
      {
        "index": 342,
        "before": [
          864,
          3216,
          177,
          11
        ],
        "after": [
          1728,
          2512,
          177,
          11
        ]
      },
      {
        "index": 343,
        "before": [
          800,
          3312,
          177,
          11
        ],
        "after": [
          992,
          2192,
          177,
          11
        ]
      },
      {
        "index": 345,
        "before": [
          608,
          2256,
          177,
          11
        ],
        "after": [
          608,
          2224,
          177,
          11
        ]
      },
      {
        "index": 346,
        "before": [
          2112,
          2608,
          177,
          11
        ],
        "after": [
          2016,
          2640,
          177,
          11
        ]
      },
      {
        "index": 353,
        "before": [
          672,
          3312,
          178,
          11
        ],
        "after": [
          960,
          2160,
          178,
          11
        ]
      },
      {
        "index": 355,
        "before": [
          736,
          3312,
          178,
          11
        ],
        "after": [
          1664,
          2608,
          178,
          11
        ]
      },
      {
        "index": 356,
        "before": [
          1248,
          2352,
          177,
          11
        ],
        "after": [
          1760,
          2480,
          177,
          11
        ]
      },
      {
        "index": 357,
        "before": [
          608,
          2288,
          177,
          11
        ],
        "after": [
          832,
          2160,
          177,
          11
        ]
      },
      {
        "index": 366,
        "before": [
          2848,
          2736,
          178,
          11
        ],
        "after": [
          2816,
          2704,
          178,
          11
        ]
      },
      {
        "index": 370,
        "before": [
          2976,
          2736,
          178,
          11
        ],
        "after": [
          3008,
          2416,
          178,
          11
        ]
      },
      {
        "index": 372,
        "before": [
          2080,
          2576,
          177,
          11
        ],
        "after": [
          2016,
          2576,
          177,
          11
        ]
      },
      {
        "index": 373,
        "before": [
          608,
          3312,
          177,
          11
        ],
        "after": [
          608,
          2256,
          177,
          11
        ]
      },
      {
        "index": 374,
        "before": [
          2912,
          2736,
          176,
          11
        ],
        "after": [
          2816,
          2672,
          176,
          11
        ]
      },
      {
        "index": 376,
        "before": [
          1088,
          2192,
          178,
          11
        ],
        "after": [
          1728,
          2320,
          178,
          11
        ]
      },
      {
        "index": 377,
        "before": [
          608,
          2224,
          177,
          11
        ],
        "after": [
          640,
          2160,
          177,
          11
        ]
      },
      {
        "index": 381,
        "before": [
          2816,
          2672,
          176,
          11
        ],
        "after": [
          2816,
          2608,
          176,
          11
        ]
      },
      {
        "index": 393,
        "before": [
          2816,
          2704,
          177,
          11
        ],
        "after": [
          2816,
          2640,
          177,
          11
        ]
      },
      {
        "index": 401,
        "before": [
          1632,
          2928,
          178,
          11
        ],
        "after": [
          1728,
          3312,
          178,
          11
        ]
      },
      {
        "index": 410,
        "before": [
          2656,
          3664,
          177,
          11
        ],
        "after": [
          2112,
          3472,
          177,
          11
        ]
      },
      {
        "index": 415,
        "before": [
          2784,
          3632,
          177,
          11
        ],
        "after": [
          2304,
          3408,
          177,
          11
        ]
      },
      {
        "index": 423,
        "before": [
          1664,
          3568,
          177,
          11
        ],
        "after": [
          1568,
          3568,
          177,
          11
        ]
      },
      {
        "index": 430,
        "before": [
          2848,
          3568,
          176,
          11
        ],
        "after": [
          2432,
          3408,
          176,
          11
        ]
      },
      {
        "index": 433,
        "before": [
          1728,
          3504,
          178,
          11
        ],
        "after": [
          1632,
          3568,
          178,
          11
        ]
      },
      {
        "index": 439,
        "before": [
          1696,
          2928,
          178,
          11
        ],
        "after": [
          1728,
          3344,
          178,
          11
        ]
      },
      {
        "index": 444,
        "before": [
          2720,
          3664,
          178,
          11
        ],
        "after": [
          2112,
          3440,
          178,
          11
        ]
      },
      {
        "index": 445,
        "before": [
          1728,
          2992,
          177,
          11
        ],
        "after": [
          1728,
          3408,
          177,
          11
        ]
      },
      {
        "index": 446,
        "before": [
          2784,
          3760,
          178,
          11
        ],
        "after": [
          2240,
          3408,
          178,
          11
        ]
      },
      {
        "index": 447,
        "before": [
          1728,
          3536,
          178,
          11
        ],
        "after": [
          1696,
          3568,
          178,
          11
        ]
      },
      {
        "index": 451,
        "before": [
          2752,
          3728,
          177,
          11
        ],
        "after": [
          2112,
          3504,
          177,
          11
        ]
      },
      {
        "index": 459,
        "before": [
          1728,
          3088,
          178,
          11
        ],
        "after": [
          1728,
          3504,
          178,
          11
        ]
      },
      {
        "index": 460,
        "before": [
          1728,
          3024,
          178,
          11
        ],
        "after": [
          1728,
          3440,
          178,
          11
        ]
      },
      {
        "index": 465,
        "before": [
          1728,
          3056,
          178,
          11
        ],
        "after": [
          1728,
          3472,
          178,
          11
        ]
      },
      {
        "index": 467,
        "before": [
          1600,
          3568,
          178,
          11
        ],
        "after": [
          1504,
          3568,
          178,
          11
        ]
      },
      {
        "index": 471,
        "before": [
          1536,
          3568,
          177,
          11
        ],
        "after": [
          1440,
          3568,
          177,
          11
        ]
      },
      {
        "index": 472,
        "before": [
          1568,
          2928,
          177,
          11
        ],
        "after": [
          1728,
          3376,
          177,
          11
        ]
      },
      {
        "index": 476,
        "before": [
          1472,
          3568,
          178,
          11
        ],
        "after": [
          1376,
          3568,
          178,
          11
        ]
      },
      {
        "index": 484,
        "before": [
          1760,
          3392,
          188,
          11
        ],
        "after": [
          1472,
          3232,
          188,
          11
        ]
      },
      {
        "index": 519,
        "before": [
          2784,
          3792,
          177,
          11
        ],
        "after": [
          2112,
          3536,
          177,
          11
        ]
      },
      {
        "index": 541,
        "before": [
          2848,
          3824,
          178,
          11
        ],
        "after": [
          2368,
          3408,
          178,
          11
        ]
      },
      {
        "index": 549,
        "before": [
          2752,
          3888,
          178,
          11
        ],
        "after": [
          2112,
          3568,
          178,
          11
        ]
      },
      {
        "index": 715,
        "before": [
          608,
          2336,
          124,
          5
        ],
        "after": [
          416,
          2432,
          124,
          5
        ]
      }
    ],
    "groups": [
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 41,
          "center": [
            3424,
            304
          ],
          "depot_type": 106,
          "owner": 1,
          "top_left_tile": [
            105,
            8
          ]
        },
        "mineral_indices": [
          10,
          12,
          32,
          6,
          1,
          13,
          3,
          25,
          39,
          20,
          2,
          18,
          21,
          8,
          0
        ],
        "gas_indices": [
          4
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 603,
          "plateau": 51,
          "depot_clearance": 33
        },
        "parent_site_index": 0,
        "group_index": 0,
        "group_sizes": [
          15
        ],
        "source_anchor": [
          3424,
          304
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              1536,
              3408
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              46,
              105
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3328,
              2448
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              102,
              75
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3008,
              2576
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              92,
              79
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1440,
              2288
            ],
            "depot_type": 106,
            "owner": 5,
            "top_left_tile": [
              43,
              70
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              320,
              2864
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              8,
              88
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2304,
              3568
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              70,
              110
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3776,
              2032
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              116,
              62
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2592,
              1488
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              79,
              45
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3648,
              1264
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              112,
              38
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2304,
              2608
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              70,
              80
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2560,
              400
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              78,
              11
            ]
          },
          {
            "kind": "expansion",
            "center": [
              96,
              1552
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              1,
              47
            ]
          },
          {
            "kind": "expansion",
            "center": [
              960,
              1712
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              28,
              52
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "maximum_minerals": 15,
        "placement_policy": "reviewed_playtest_layout"
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 116,
          "center": [
            448,
            560
          ],
          "depot_type": 106,
          "owner": 6,
          "top_left_tile": [
            12,
            16
          ]
        },
        "mineral_indices": [
          105,
          115,
          72,
          93,
          75,
          120,
          54,
          92,
          83,
          67,
          73,
          74,
          53,
          50,
          51
        ],
        "gas_indices": [
          84
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 11,
          "gas_exit": 3
        },
        "parent_site_index": 1,
        "group_index": 0,
        "group_sizes": [
          15
        ],
        "source_anchor": [
          448,
          560
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              1536,
              3408
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              46,
              105
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3328,
              2448
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              102,
              75
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3008,
              2576
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              92,
              79
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1440,
              2288
            ],
            "depot_type": 106,
            "owner": 5,
            "top_left_tile": [
              43,
              70
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              320,
              2864
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              8,
              88
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2304,
              3568
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              70,
              110
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3776,
              2032
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              116,
              62
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2592,
              1488
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              79,
              45
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3648,
              1264
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              112,
              38
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2304,
              2608
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              70,
              80
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2560,
              400
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              78,
              11
            ]
          },
          {
            "kind": "expansion",
            "center": [
              96,
              1552
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              1,
              47
            ]
          },
          {
            "kind": "expansion",
            "center": [
              960,
              1712
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              28,
              52
            ]
          }
        ],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "maximum_minerals": 15,
        "placement_policy": "reviewed_playtest_layout"
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            1536,
            3408
          ],
          "depot_type": 131,
          "owner": null,
          "top_left_tile": [
            46,
            105
          ]
        },
        "mineral_indices": [
          471,
          467,
          476,
          447,
          423,
          433,
          401,
          439,
          445,
          460,
          465,
          459,
          472
        ],
        "gas_indices": [
          484
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 1
        },
        "parent_site_index": 2,
        "group_index": 0,
        "group_sizes": [
          13
        ],
        "source_anchor": [
          1536,
          3408
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              1536,
              3408
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              46,
              105
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3328,
              2448
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              102,
              75
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3008,
              2576
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              92,
              79
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1440,
              2288
            ],
            "depot_type": 106,
            "owner": 5,
            "top_left_tile": [
              43,
              70
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              320,
              2864
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              8,
              88
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2304,
              3568
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              70,
              110
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3776,
              2032
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              116,
              62
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2592,
              1488
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              79,
              45
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3648,
              1264
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              112,
              38
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2304,
              2608
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              70,
              80
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2560,
              400
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              78,
              11
            ]
          },
          {
            "kind": "expansion",
            "center": [
              96,
              1552
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              1,
              47
            ]
          },
          {
            "kind": "expansion",
            "center": [
              960,
              1712
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              28,
              52
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "maximum_minerals": 13,
        "placement_policy": "reviewed_playtest_layout"
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 488,
          "center": [
            3584,
            3696
          ],
          "depot_type": 106,
          "owner": 0,
          "top_left_tile": [
            110,
            114
          ]
        },
        "mineral_indices": [
          523,
          531,
          524,
          520,
          521,
          528,
          532,
          525,
          527,
          510,
          518
        ],
        "gas_indices": [
          501
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 1003,
          "geometry": 213,
          "gas_exit": 1
        },
        "parent_site_index": 3,
        "group_index": 0,
        "group_sizes": [
          11
        ],
        "source_anchor": [
          3584,
          3696
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              1536,
              3408
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              46,
              105
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3328,
              2448
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              102,
              75
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3008,
              2576
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              92,
              79
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1440,
              2288
            ],
            "depot_type": 106,
            "owner": 5,
            "top_left_tile": [
              43,
              70
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              320,
              2864
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              8,
              88
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2304,
              3568
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              70,
              110
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3776,
              2032
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              116,
              62
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2592,
              1488
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              79,
              45
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3648,
              1264
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              112,
              38
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2304,
              2608
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              70,
              80
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2560,
              400
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              78,
              11
            ]
          },
          {
            "kind": "expansion",
            "center": [
              96,
              1552
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              1,
              47
            ]
          },
          {
            "kind": "expansion",
            "center": [
              960,
              1712
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              28,
              52
            ]
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            3328,
            2448
          ],
          "depot_type": 131,
          "owner": null,
          "top_left_tile": [
            102,
            75
          ]
        },
        "mineral_indices": [
          330,
          362,
          390,
          326,
          361,
          363,
          391,
          319,
          320
        ],
        "gas_indices": [
          322
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 96,
          "depot_clearance": 338,
          "army_route": 52,
          "gas_exit": 19,
          "gas_inside_bank": 11
        },
        "parent_site_index": 4,
        "group_index": 0,
        "group_sizes": [
          9,
          10
        ],
        "source_anchor": [
          3328,
          2448
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              1536,
              3408
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              46,
              105
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3328,
              2448
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              102,
              75
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3008,
              2576
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              92,
              79
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1440,
              2288
            ],
            "depot_type": 106,
            "owner": 5,
            "top_left_tile": [
              43,
              70
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              320,
              2864
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              8,
              88
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2304,
              3568
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              70,
              110
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3776,
              2032
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              116,
              62
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2592,
              1488
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              79,
              45
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3648,
              1264
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              112,
              38
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2304,
              2608
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              70,
              80
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2560,
              400
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              78,
              11
            ]
          },
          {
            "kind": "expansion",
            "center": [
              96,
              1552
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              1,
              47
            ]
          },
          {
            "kind": "expansion",
            "center": [
              960,
              1712
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              28,
              52
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "skipped_arc_slots": 2,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            3008,
            2576
          ],
          "depot_type": 131,
          "owner": null,
          "top_left_tile": [
            92,
            79
          ],
          "additional_group_depot": true
        },
        "mineral_indices": [
          393,
          381,
          325,
          318,
          327,
          366,
          374,
          370,
          314,
          321
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 30
        },
        "parent_site_index": 4,
        "group_index": 1,
        "group_sizes": [
          9,
          10
        ],
        "source_anchor": [
          3328,
          2448
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              1536,
              3408
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              46,
              105
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3328,
              2448
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              102,
              75
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3008,
              2576
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              92,
              79
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1440,
              2288
            ],
            "depot_type": 106,
            "owner": 5,
            "top_left_tile": [
              43,
              70
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              320,
              2864
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              8,
              88
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2304,
              3568
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              70,
              110
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3776,
              2032
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              116,
              62
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2592,
              1488
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              79,
              45
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3648,
              1264
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              112,
              38
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2304,
              2608
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              70,
              80
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2560,
              400
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              78,
              11
            ]
          },
          {
            "kind": "expansion",
            "center": [
              96,
              1552
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              1,
              47
            ]
          },
          {
            "kind": "expansion",
            "center": [
              960,
              1712
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              28,
              52
            ]
          }
        ],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 198,
          "center": [
            1824,
            1104
          ],
          "depot_type": 106,
          "owner": 4,
          "top_left_tile": [
            55,
            33
          ]
        },
        "mineral_indices": [
          174,
          178,
          185,
          197,
          179,
          177,
          184,
          192
        ],
        "gas_indices": [
          165
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 311,
          "plateau": 421
        },
        "parent_site_index": 5,
        "group_index": 0,
        "group_sizes": [
          8
        ],
        "source_anchor": [
          1824,
          1104
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              1536,
              3408
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              46,
              105
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3328,
              2448
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              102,
              75
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3008,
              2576
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              92,
              79
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1440,
              2288
            ],
            "depot_type": 106,
            "owner": 5,
            "top_left_tile": [
              43,
              70
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              320,
              2864
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              8,
              88
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2304,
              3568
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              70,
              110
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3776,
              2032
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              116,
              62
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2592,
              1488
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              79,
              45
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3648,
              1264
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              112,
              38
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2304,
              2608
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              70,
              80
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2560,
              400
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              78,
              11
            ]
          },
          {
            "kind": "expansion",
            "center": [
              96,
              1552
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              1,
              47
            ]
          },
          {
            "kind": "expansion",
            "center": [
              960,
              1712
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              28,
              52
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 331,
          "center": [
            800,
            2320
          ],
          "depot_type": 106,
          "owner": 5,
          "top_left_tile": [
            23,
            71
          ]
        },
        "mineral_indices": [
          345,
          357,
          347,
          377,
          295,
          296,
          373,
          343,
          353
        ],
        "gas_indices": [
          315
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 9,
          "plateau": 13,
          "gas_lane": 30,
          "gas_exit": 2
        },
        "parent_site_index": 6,
        "group_index": 0,
        "group_sizes": [
          9,
          9
        ],
        "source_anchor": [
          800,
          2320
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              1536,
              3408
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              46,
              105
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3328,
              2448
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              102,
              75
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3008,
              2576
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              92,
              79
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1440,
              2288
            ],
            "depot_type": 106,
            "owner": 5,
            "top_left_tile": [
              43,
              70
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              320,
              2864
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              8,
              88
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2304,
              3568
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              70,
              110
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3776,
              2032
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              116,
              62
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2592,
              1488
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              79,
              45
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3648,
              1264
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              112,
              38
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2304,
              2608
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              70,
              80
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2560,
              400
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              78,
              11
            ]
          },
          {
            "kind": "expansion",
            "center": [
              96,
              1552
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              1,
              47
            ]
          },
          {
            "kind": "expansion",
            "center": [
              960,
              1712
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              28,
              52
            ]
          }
        ],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "maximum_minerals": 12,
        "placement_policy": "reviewed_playtest_layout"
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            1440,
            2288
          ],
          "depot_type": 106,
          "owner": 5,
          "top_left_tile": [
            43,
            70
          ],
          "additional_group_depot": true
        },
        "mineral_indices": [
          300,
          301,
          293,
          376,
          303,
          356,
          342,
          355,
          302
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 215,
          "plateau": 236,
          "army_route": 7,
          "original_displacement": 4
        },
        "parent_site_index": 6,
        "group_index": 1,
        "group_sizes": [
          9,
          9
        ],
        "source_anchor": [
          800,
          2320
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              1536,
              3408
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              46,
              105
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3328,
              2448
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              102,
              75
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3008,
              2576
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              92,
              79
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1440,
              2288
            ],
            "depot_type": 106,
            "owner": 5,
            "top_left_tile": [
              43,
              70
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              320,
              2864
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              8,
              88
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2304,
              3568
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              70,
              110
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3776,
              2032
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              116,
              62
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2592,
              1488
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              79,
              45
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3648,
              1264
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              112,
              38
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2304,
              2608
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              70,
              80
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2560,
              400
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              78,
              11
            ]
          },
          {
            "kind": "expansion",
            "center": [
              96,
              1552
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              1,
              47
            ]
          },
          {
            "kind": "expansion",
            "center": [
              960,
              1712
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              28,
              52
            ]
          }
        ],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "maximum_minerals": 12,
        "placement_policy": "reviewed_playtest_layout"
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            320,
            2864
          ],
          "depot_type": 131,
          "owner": null,
          "top_left_tile": [
            8,
            88
          ]
        },
        "mineral_indices": [
          375,
          371,
          379,
          389,
          388,
          392,
          382
        ],
        "gas_indices": [
          359
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "army_route": 12,
          "plateau": 1,
          "geometry": 1
        },
        "parent_site_index": 7,
        "group_index": 0,
        "group_sizes": [
          7
        ],
        "source_anchor": [
          320,
          2864
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              1536,
              3408
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              46,
              105
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3328,
              2448
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              102,
              75
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3008,
              2576
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              92,
              79
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1440,
              2288
            ],
            "depot_type": 106,
            "owner": 5,
            "top_left_tile": [
              43,
              70
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              320,
              2864
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              8,
              88
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2304,
              3568
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              70,
              110
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3776,
              2032
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              116,
              62
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2592,
              1488
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              79,
              45
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3648,
              1264
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              112,
              38
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2304,
              2608
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              70,
              80
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2560,
              400
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              78,
              11
            ]
          },
          {
            "kind": "expansion",
            "center": [
              96,
              1552
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              1,
              47
            ]
          },
          {
            "kind": "expansion",
            "center": [
              960,
              1712
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              28,
              52
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            2304,
            3568
          ],
          "depot_type": 131,
          "owner": null,
          "top_left_tile": [
            70,
            110
          ]
        },
        "mineral_indices": [
          430,
          451,
          446,
          519,
          415,
          410,
          541,
          549,
          444
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 925,
          "geometry": 1
        },
        "parent_site_index": 8,
        "group_index": 0,
        "group_sizes": [
          9
        ],
        "source_anchor": [
          2560,
          3824
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              1536,
              3408
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              46,
              105
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3328,
              2448
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              102,
              75
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3008,
              2576
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              92,
              79
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1440,
              2288
            ],
            "depot_type": 106,
            "owner": 5,
            "top_left_tile": [
              43,
              70
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              320,
              2864
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              8,
              88
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2304,
              3568
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              70,
              110
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3776,
              2032
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              116,
              62
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2592,
              1488
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              79,
              45
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3648,
              1264
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              112,
              38
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2304,
              2608
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              70,
              80
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2560,
              400
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              78,
              11
            ]
          },
          {
            "kind": "expansion",
            "center": [
              96,
              1552
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              1,
              47
            ]
          },
          {
            "kind": "expansion",
            "center": [
              960,
              1712
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              28,
              52
            ]
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            3776,
            2032
          ],
          "depot_type": 131,
          "owner": null,
          "top_left_tile": [
            116,
            62
          ]
        },
        "mineral_indices": [
          294,
          267,
          288,
          270,
          299,
          307,
          269,
          292
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 19,
          "geometry": 7,
          "army_route": 4
        },
        "parent_site_index": 9,
        "group_index": 0,
        "group_sizes": [
          8
        ],
        "source_anchor": [
          3776,
          2032
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              1536,
              3408
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              46,
              105
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3328,
              2448
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              102,
              75
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3008,
              2576
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              92,
              79
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1440,
              2288
            ],
            "depot_type": 106,
            "owner": 5,
            "top_left_tile": [
              43,
              70
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              320,
              2864
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              8,
              88
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2304,
              3568
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              70,
              110
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3776,
              2032
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              116,
              62
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2592,
              1488
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              79,
              45
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3648,
              1264
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              112,
              38
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2304,
              2608
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              70,
              80
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2560,
              400
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              78,
              11
            ]
          },
          {
            "kind": "expansion",
            "center": [
              96,
              1552
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              1,
              47
            ]
          },
          {
            "kind": "expansion",
            "center": [
              960,
              1712
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              28,
              52
            ]
          }
        ],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            2592,
            1488
          ],
          "depot_type": 131,
          "owner": null,
          "top_left_tile": [
            79,
            45
          ]
        },
        "mineral_indices": [
          262,
          265,
          266,
          241,
          246,
          287,
          286,
          264,
          278,
          274
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 387,
          "geometry": 169,
          "army_route": 9,
          "mineral_bank_split": 5
        },
        "parent_site_index": 10,
        "group_index": 0,
        "group_sizes": [
          10
        ],
        "source_anchor": [
          2592,
          1488
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              1536,
              3408
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              46,
              105
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3328,
              2448
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              102,
              75
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3008,
              2576
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              92,
              79
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1440,
              2288
            ],
            "depot_type": 106,
            "owner": 5,
            "top_left_tile": [
              43,
              70
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              320,
              2864
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              8,
              88
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2304,
              3568
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              70,
              110
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3776,
              2032
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              116,
              62
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2592,
              1488
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              79,
              45
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3648,
              1264
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              112,
              38
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2304,
              2608
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              70,
              80
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2560,
              400
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              78,
              11
            ]
          },
          {
            "kind": "expansion",
            "center": [
              96,
              1552
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              1,
              47
            ]
          },
          {
            "kind": "expansion",
            "center": [
              960,
              1712
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              28,
              52
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "skipped_arc_slots": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            3648,
            1264
          ],
          "depot_type": 131,
          "owner": null,
          "top_left_tile": [
            112,
            38
          ]
        },
        "mineral_indices": [
          203,
          200,
          205
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 31,
          "geometry": 10
        },
        "parent_site_index": 11,
        "group_index": 0,
        "group_sizes": [
          3
        ],
        "source_anchor": [
          3680,
          1264
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              1536,
              3408
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              46,
              105
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3328,
              2448
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              102,
              75
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3008,
              2576
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              92,
              79
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1440,
              2288
            ],
            "depot_type": 106,
            "owner": 5,
            "top_left_tile": [
              43,
              70
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              320,
              2864
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              8,
              88
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2304,
              3568
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              70,
              110
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3776,
              2032
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              116,
              62
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2592,
              1488
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              79,
              45
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3648,
              1264
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              112,
              38
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2304,
              2608
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              70,
              80
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2560,
              400
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              78,
              11
            ]
          },
          {
            "kind": "expansion",
            "center": [
              96,
              1552
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              1,
              47
            ]
          },
          {
            "kind": "expansion",
            "center": [
              960,
              1712
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              28,
              52
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            2304,
            2608
          ],
          "depot_type": 131,
          "owner": null,
          "top_left_tile": [
            70,
            80
          ]
        },
        "mineral_indices": [
          346,
          372,
          336,
          338
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 154
        },
        "parent_site_index": 12,
        "group_index": 0,
        "group_sizes": [
          4
        ],
        "source_anchor": [
          2304,
          2608
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              1536,
              3408
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              46,
              105
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3328,
              2448
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              102,
              75
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3008,
              2576
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              92,
              79
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1440,
              2288
            ],
            "depot_type": 106,
            "owner": 5,
            "top_left_tile": [
              43,
              70
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              320,
              2864
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              8,
              88
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2304,
              3568
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              70,
              110
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3776,
              2032
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              116,
              62
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2592,
              1488
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              79,
              45
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3648,
              1264
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              112,
              38
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2304,
              2608
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              70,
              80
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2560,
              400
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              78,
              11
            ]
          },
          {
            "kind": "expansion",
            "center": [
              96,
              1552
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              1,
              47
            ]
          },
          {
            "kind": "expansion",
            "center": [
              960,
              1712
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              28,
              52
            ]
          }
        ],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            2560,
            400
          ],
          "depot_type": 131,
          "owner": null,
          "top_left_tile": [
            78,
            11
          ]
        },
        "mineral_indices": [
          24,
          17
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 5,
          "geometry": 8
        },
        "parent_site_index": 13,
        "group_index": 0,
        "group_sizes": [
          2
        ],
        "source_anchor": [
          2560,
          400
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              1536,
              3408
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              46,
              105
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3328,
              2448
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              102,
              75
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3008,
              2576
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              92,
              79
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1440,
              2288
            ],
            "depot_type": 106,
            "owner": 5,
            "top_left_tile": [
              43,
              70
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              320,
              2864
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              8,
              88
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2304,
              3568
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              70,
              110
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3776,
              2032
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              116,
              62
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2592,
              1488
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              79,
              45
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3648,
              1264
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              112,
              38
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2304,
              2608
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              70,
              80
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2560,
              400
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              78,
              11
            ]
          },
          {
            "kind": "expansion",
            "center": [
              96,
              1552
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              1,
              47
            ]
          },
          {
            "kind": "expansion",
            "center": [
              960,
              1712
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              28,
              52
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            96,
            1552
          ],
          "depot_type": 131,
          "owner": null,
          "top_left_tile": [
            1,
            47
          ]
        },
        "mineral_indices": [
          226,
          277
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {
          "army_route": 2,
          "plateau": 2
        },
        "parent_site_index": 14,
        "group_index": 0,
        "group_sizes": [
          2
        ],
        "source_anchor": [
          96,
          1552
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              1536,
              3408
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              46,
              105
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3328,
              2448
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              102,
              75
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3008,
              2576
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              92,
              79
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1440,
              2288
            ],
            "depot_type": 106,
            "owner": 5,
            "top_left_tile": [
              43,
              70
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              320,
              2864
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              8,
              88
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2304,
              3568
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              70,
              110
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3776,
              2032
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              116,
              62
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2592,
              1488
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              79,
              45
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3648,
              1264
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              112,
              38
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2304,
              2608
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              70,
              80
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2560,
              400
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              78,
              11
            ]
          },
          {
            "kind": "expansion",
            "center": [
              96,
              1552
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              1,
              47
            ]
          },
          {
            "kind": "expansion",
            "center": [
              960,
              1712
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              28,
              52
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            960,
            1712
          ],
          "depot_type": 131,
          "owner": null,
          "top_left_tile": [
            28,
            52
          ]
        },
        "mineral_indices": [
          261
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {},
        "parent_site_index": 15,
        "group_index": 0,
        "group_sizes": [
          1
        ],
        "source_anchor": [
          960,
          1712
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              1536,
              3408
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              46,
              105
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3328,
              2448
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              102,
              75
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3008,
              2576
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              92,
              79
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              1440,
              2288
            ],
            "depot_type": 106,
            "owner": 5,
            "top_left_tile": [
              43,
              70
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              320,
              2864
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              8,
              88
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2304,
              3568
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              70,
              110
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3776,
              2032
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              116,
              62
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2592,
              1488
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              79,
              45
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3648,
              1264
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              112,
              38
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2304,
              2608
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              70,
              80
            ]
          },
          {
            "kind": "expansion",
            "center": [
              2560,
              400
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              78,
              11
            ]
          },
          {
            "kind": "expansion",
            "center": [
              96,
              1552
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              1,
              47
            ]
          },
          {
            "kind": "expansion",
            "center": [
              960,
              1712
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              28,
              52
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      }
    ]
  },
  "604": {
    "input_unit_sha256": "08b82e350041c70c3f6090e18116f8d3c84f3afc8b04a21a84b34a7b9d299c00",
    "moves": [
      {
        "index": 9,
        "before": [
          576,
          560,
          178,
          11
        ],
        "after": [
          416,
          112,
          178,
          11
        ]
      },
      {
        "index": 10,
        "before": [
          704,
          176,
          176,
          11
        ],
        "after": [
          736,
          144,
          176,
          11
        ]
      },
      {
        "index": 13,
        "before": [
          640,
          144,
          177,
          11
        ],
        "after": [
          672,
          144,
          177,
          11
        ]
      },
      {
        "index": 20,
        "before": [
          576,
          144,
          176,
          11
        ],
        "after": [
          288,
          176,
          176,
          11
        ]
      },
      {
        "index": 21,
        "before": [
          704,
          208,
          177,
          11
        ],
        "after": [
          768,
          176,
          177,
          11
        ]
      },
      {
        "index": 24,
        "before": [
          768,
          656,
          178,
          11
        ],
        "after": [
          608,
          112,
          178,
          11
        ]
      },
      {
        "index": 29,
        "before": [
          832,
          656,
          177,
          11
        ],
        "after": [
          768,
          240,
          177,
          11
        ]
      },
      {
        "index": 30,
        "before": [
          288,
          224,
          149,
          4
        ],
        "after": [
          736,
          352,
          149,
          4
        ]
      },
      {
        "index": 37,
        "before": [
          704,
          656,
          176,
          11
        ],
        "after": [
          544,
          112,
          176,
          11
        ]
      },
      {
        "index": 45,
        "before": [
          640,
          656,
          177,
          11
        ],
        "after": [
          480,
          112,
          177,
          11
        ]
      },
      {
        "index": 56,
        "before": [
          448,
          144,
          177,
          11
        ],
        "after": [
          224,
          240,
          177,
          11
        ]
      },
      {
        "index": 57,
        "before": [
          576,
          528,
          177,
          11
        ],
        "after": [
          352,
          144,
          177,
          11
        ]
      },
      {
        "index": 61,
        "before": [
          576,
          592,
          177,
          11
        ],
        "after": [
          320,
          272,
          177,
          11
        ]
      },
      {
        "index": 73,
        "before": [
          512,
          144,
          178,
          11
        ],
        "after": [
          256,
          208,
          178,
          11
        ]
      },
      {
        "index": 508,
        "before": [
          5888,
          1488,
          131,
          3
        ],
        "after": [
          5664,
          1328,
          131,
          3
        ]
      },
      {
        "index": 509,
        "before": [
          5696,
          1552,
          131,
          3
        ],
        "after": [
          5600,
          1552,
          131,
          3
        ]
      }
    ],
    "groups": [
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 484,
          "center": [
            512,
            304
          ],
          "depot_type": 133,
          "owner": 4,
          "top_left_tile": [
            14,
            8
          ]
        },
        "mineral_indices": [
          13,
          20,
          56,
          73,
          21,
          10,
          24,
          29,
          37,
          45,
          57,
          61,
          9
        ],
        "gas_indices": [
          30
        ],
        "status": "ladder_separate_gas",
        "reasons": {},
        "parent_site_index": 0,
        "group_index": 0,
        "group_sizes": [
          13
        ],
        "source_anchor": [
          512,
          304
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5216,
              304
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              161,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              4000,
              80
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              123,
              1
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "maximum_minerals": 13,
        "placement_policy": "reviewed_playtest_layout"
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 48,
          "center": [
            2400,
            240
          ],
          "depot_type": 106,
          "owner": 1,
          "top_left_tile": [
            73,
            6
          ]
        },
        "mineral_indices": [
          1,
          60,
          15,
          43,
          0,
          7,
          8,
          47,
          68,
          23,
          25,
          44
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 46,
          "plateau": 12
        },
        "parent_site_index": 1,
        "group_index": 0,
        "group_sizes": [
          12
        ],
        "source_anchor": [
          2400,
          240
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5216,
              304
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              161,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              4000,
              80
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              123,
              1
            ]
          }
        ],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            5216,
            304
          ],
          "depot_type": 131,
          "owner": null,
          "top_left_tile": [
            161,
            8
          ]
        },
        "mineral_indices": [
          145,
          78,
          91,
          132,
          97,
          115,
          79,
          92,
          146,
          69
        ],
        "gas_indices": [
          174
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 35,
          "geometry": 19
        },
        "parent_site_index": 2,
        "group_index": 0,
        "group_sizes": [
          10
        ],
        "source_anchor": [
          5216,
          304
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5216,
              304
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              161,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              4000,
              80
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              123,
              1
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 357,
          "center": [
            416,
            1616
          ],
          "depot_type": 106,
          "owner": 6,
          "top_left_tile": [
            11,
            49
          ]
        },
        "mineral_indices": [
          452,
          437,
          461,
          419,
          438,
          456,
          470,
          422,
          423,
          407
        ],
        "gas_indices": [
          443
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 168,
          "geometry": 62,
          "gas_exit": 2
        },
        "parent_site_index": 3,
        "group_index": 0,
        "group_sizes": [
          10
        ],
        "source_anchor": [
          416,
          1616
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5216,
              304
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              161,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              4000,
              80
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              123,
              1
            ]
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 513,
          "center": [
            5888,
            1648
          ],
          "depot_type": 131,
          "owner": 3,
          "top_left_tile": [
            182,
            50
          ]
        },
        "mineral_indices": [
          465,
          475,
          459,
          449,
          457,
          434,
          467,
          446,
          466
        ],
        "gas_indices": [
          476
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 22,
          "geometry": 24
        },
        "parent_site_index": 4,
        "group_index": 0,
        "group_sizes": [
          9
        ],
        "source_anchor": [
          5888,
          1648
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5216,
              304
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              161,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              4000,
              80
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              123,
              1
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 398,
          "center": [
            3456,
            1744
          ],
          "depot_type": 106,
          "owner": 1,
          "top_left_tile": [
            106,
            53
          ]
        },
        "mineral_indices": [
          247,
          261,
          269,
          270,
          334,
          252,
          253,
          341,
          260,
          342,
          259
        ],
        "gas_indices": [
          337
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 56
        },
        "parent_site_index": 5,
        "group_index": 0,
        "group_sizes": [
          11
        ],
        "source_anchor": [
          3456,
          1744
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5216,
              304
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              161,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              4000,
              80
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              123,
              1
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            4000,
            80
          ],
          "depot_type": 131,
          "owner": null,
          "top_left_tile": [
            123,
            1
          ]
        },
        "mineral_indices": [
          70,
          80,
          81,
          82,
          71
        ],
        "gas_indices": [
          99
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 104
        },
        "parent_site_index": 6,
        "group_index": 0,
        "group_sizes": [
          5
        ],
        "source_anchor": [
          4000,
          80
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5216,
              304
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              161,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              4000,
              80
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              123,
              1
            ]
          }
        ],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      }
    ]
  },
  "605": {
    "input_unit_sha256": "1c7eaa9ea8e89d94c8bda2220d2d10c0e7c89031c89cf0aaa0780b4bc1bdfb90",
    "moves": [
      {
        "index": 236,
        "before": [
          3136,
          3104,
          157,
          1
        ],
        "after": [
          3072,
          3136,
          157,
          1
        ]
      },
      {
        "index": 238,
        "before": [
          2464,
          2704,
          177,
          11
        ],
        "after": [
          2784,
          2736,
          177,
          11
        ]
      },
      {
        "index": 240,
        "before": [
          2400,
          2768,
          176,
          11
        ],
        "after": [
          2688,
          2864,
          176,
          11
        ]
      },
      {
        "index": 241,
        "before": [
          2784,
          2960,
          178,
          11
        ],
        "after": [
          2976,
          2736,
          178,
          11
        ]
      },
      {
        "index": 242,
        "before": [
          2784,
          2992,
          178,
          11
        ],
        "after": [
          2688,
          2992,
          178,
          11
        ]
      },
      {
        "index": 243,
        "before": [
          2528,
          2704,
          178,
          11
        ],
        "after": [
          2848,
          2704,
          178,
          11
        ]
      },
      {
        "index": 244,
        "before": [
          2400,
          2736,
          178,
          11
        ],
        "after": [
          2752,
          2768,
          178,
          11
        ]
      },
      {
        "index": 245,
        "before": [
          2400,
          2864,
          178,
          11
        ],
        "after": [
          2688,
          2960,
          178,
          11
        ]
      },
      {
        "index": 246,
        "before": [
          2784,
          3024,
          178,
          11
        ],
        "after": [
          2720,
          3024,
          178,
          11
        ]
      },
      {
        "index": 247,
        "before": [
          2976,
          3088,
          178,
          11
        ],
        "after": [
          3104,
          2736,
          178,
          11
        ]
      },
      {
        "index": 248,
        "before": [
          2400,
          2800,
          178,
          11
        ],
        "after": [
          2656,
          2896,
          178,
          11
        ]
      },
      {
        "index": 249,
        "before": [
          2784,
          2928,
          178,
          11
        ],
        "after": [
          2912,
          2704,
          178,
          11
        ]
      },
      {
        "index": 250,
        "before": [
          2400,
          2832,
          176,
          11
        ],
        "after": [
          2656,
          2928,
          176,
          11
        ]
      },
      {
        "index": 251,
        "before": [
          2912,
          3088,
          178,
          11
        ],
        "after": [
          3040,
          2736,
          178,
          11
        ]
      },
      {
        "index": 252,
        "before": [
          2848,
          3088,
          177,
          11
        ],
        "after": [
          2720,
          3056,
          177,
          11
        ]
      },
      {
        "index": 468,
        "before": [
          3584,
          5424,
          178,
          11
        ],
        "after": [
          3488,
          5744,
          178,
          11
        ]
      },
      {
        "index": 476,
        "before": [
          3648,
          5424,
          178,
          11
        ],
        "after": [
          3680,
          5680,
          178,
          11
        ]
      },
      {
        "index": 477,
        "before": [
          3680,
          5488,
          178,
          11
        ],
        "after": [
          3808,
          5808,
          178,
          11
        ]
      },
      {
        "index": 479,
        "before": [
          3520,
          5424,
          177,
          11
        ],
        "after": [
          3552,
          5680,
          177,
          11
        ]
      },
      {
        "index": 486,
        "before": [
          3808,
          6064,
          177,
          11
        ],
        "after": [
          3776,
          6064,
          177,
          11
        ]
      },
      {
        "index": 492,
        "before": [
          3808,
          6000,
          178,
          11
        ],
        "after": [
          3840,
          5904,
          178,
          11
        ]
      },
      {
        "index": 496,
        "before": [
          3680,
          5552,
          177,
          11
        ],
        "after": [
          3744,
          5712,
          177,
          11
        ]
      },
      {
        "index": 499,
        "before": [
          3680,
          6064,
          176,
          11
        ],
        "after": [
          3840,
          5968,
          176,
          11
        ]
      },
      {
        "index": 500,
        "before": [
          3680,
          5584,
          178,
          11
        ],
        "after": [
          3616,
          5680,
          178,
          11
        ]
      },
      {
        "index": 501,
        "before": [
          3808,
          5904,
          178,
          11
        ],
        "after": [
          3808,
          5840,
          178,
          11
        ]
      },
      {
        "index": 503,
        "before": [
          3744,
          6064,
          177,
          11
        ],
        "after": [
          3712,
          6096,
          177,
          11
        ]
      },
      {
        "index": 504,
        "before": [
          3680,
          5520,
          177,
          11
        ],
        "after": [
          3808,
          5712,
          177,
          11
        ]
      },
      {
        "index": 506,
        "before": [
          3808,
          5872,
          178,
          11
        ],
        "after": [
          3840,
          5872,
          178,
          11
        ]
      },
      {
        "index": 511,
        "before": [
          2560,
          592,
          131,
          5
        ],
        "after": [
          2656,
          688,
          131,
          5
        ]
      }
    ],
    "groups": [
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 227,
          "center": [
            2976,
            2928
          ],
          "depot_type": 154,
          "owner": 1,
          "top_left_tile": [
            91,
            90
          ]
        },
        "mineral_indices": [
          242,
          246,
          241,
          247,
          249,
          252,
          251,
          248,
          240,
          245,
          244,
          238,
          243,
          250
        ],
        "gas_indices": [
          236
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 8,
          "gas_exit": 2,
          "gas_lane": 4
        },
        "parent_site_index": 0,
        "group_index": 0,
        "group_sizes": [
          14
        ],
        "source_anchor": [
          2976,
          2928
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              3776,
              1648
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              116,
              50
            ]
          }
        ],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "maximum_minerals": 14,
        "placement_policy": "reviewed_playtest_layout"
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 469,
          "center": [
            3616,
            5904
          ],
          "depot_type": 154,
          "owner": 1,
          "top_left_tile": [
            111,
            183
          ]
        },
        "mineral_indices": [
          484,
          499,
          506,
          503,
          492,
          501,
          486,
          479,
          468,
          504,
          476,
          477,
          496,
          500
        ],
        "gas_indices": [
          470
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 21,
          "plateau": 11,
          "depot_clearance": 12,
          "gas_lane": 2,
          "army_route": 1
        },
        "parent_site_index": 1,
        "group_index": 0,
        "group_sizes": [
          14
        ],
        "source_anchor": [
          3616,
          5904
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              3776,
              1648
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              116,
              50
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "maximum_minerals": 14,
        "placement_policy": "reviewed_playtest_layout"
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 324,
          "center": [
            448,
            4592
          ],
          "depot_type": 106,
          "owner": 0,
          "top_left_tile": [
            12,
            142
          ]
        },
        "mineral_indices": [
          343,
          359,
          370,
          350,
          342,
          349,
          372,
          351,
          366,
          365,
          360,
          367
        ],
        "gas_indices": [
          352
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 9,
          "plateau": 49
        },
        "parent_site_index": 2,
        "group_index": 0,
        "group_sizes": [
          12
        ],
        "source_anchor": [
          448,
          4592
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              3776,
              1648
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              116,
              50
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 508,
          "center": [
            2464,
            368
          ],
          "depot_type": 131,
          "owner": 5,
          "top_left_tile": [
            75,
            10
          ]
        },
        "mineral_indices": [
          11,
          25,
          2,
          1,
          13,
          33,
          3,
          10,
          5,
          6,
          21
        ],
        "gas_indices": [
          20,
          570
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 56,
          "gas_inside_bank": 92,
          "resource_overlap": 3
        },
        "parent_site_index": 3,
        "group_index": 0,
        "group_sizes": [
          11
        ],
        "source_anchor": [
          2464,
          368
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              3776,
              1648
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              116,
              50
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            3776,
            1648
          ],
          "depot_type": 131,
          "owner": null,
          "top_left_tile": [
            116,
            50
          ]
        },
        "mineral_indices": [
          121,
          120,
          122,
          115,
          114,
          116,
          113,
          117,
          119,
          124,
          112
        ],
        "gas_indices": [
          127
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 2
        },
        "parent_site_index": 4,
        "group_index": 0,
        "group_sizes": [
          11
        ],
        "source_anchor": [
          3776,
          1648
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              3776,
              1648
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              116,
              50
            ]
          }
        ],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 173,
          "center": [
            512,
            2544
          ],
          "depot_type": 106,
          "owner": 0,
          "top_left_tile": [
            14,
            78
          ]
        },
        "mineral_indices": [
          206,
          205,
          191,
          181,
          200,
          189,
          204,
          196,
          185,
          195,
          180
        ],
        "gas_indices": [
          171
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 53,
          "gas_exit": 72,
          "gas_lane": 52,
          "plateau": 3
        },
        "parent_site_index": 5,
        "group_index": 0,
        "group_sizes": [
          11
        ],
        "source_anchor": [
          512,
          2544
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              3776,
              1648
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              116,
              50
            ]
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 61,
          "center": [
            480,
            560
          ],
          "depot_type": 106,
          "owner": 0,
          "top_left_tile": [
            13,
            16
          ]
        },
        "mineral_indices": [
          56,
          37,
          48,
          55,
          39,
          43,
          41,
          44,
          34,
          38
        ],
        "gas_indices": [
          70
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 29,
          "plateau": 25,
          "gas_lane": 32,
          "gas_exit": 4
        },
        "parent_site_index": 6,
        "group_index": 0,
        "group_sizes": [
          10
        ],
        "source_anchor": [
          480,
          560
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              3776,
              1648
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              116,
              50
            ]
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      }
    ]
  },
  "606": {
    "input_unit_sha256": "e6ba938fe6e7904bb9ececa3e78d47fbf4fb1e739487455e05039a7f3d3a7891",
    "moves": [
      {
        "index": 346,
        "before": [
          320,
          3920,
          176,
          11
        ],
        "after": [
          288,
          3856,
          176,
          11
        ]
      },
      {
        "index": 351,
        "before": [
          256,
          3744,
          149,
          5
        ],
        "after": [
          704,
          3776,
          149,
          5
        ]
      },
      {
        "index": 353,
        "before": [
          1024,
          3376,
          177,
          11
        ],
        "after": [
          288,
          3760,
          177,
          11
        ]
      },
      {
        "index": 363,
        "before": [
          288,
          3856,
          176,
          11
        ],
        "after": [
          288,
          3792,
          176,
          11
        ]
      },
      {
        "index": 370,
        "before": [
          1024,
          3408,
          177,
          11
        ],
        "after": [
          448,
          3920,
          177,
          11
        ]
      },
      {
        "index": 371,
        "before": [
          288,
          3888,
          178,
          11
        ],
        "after": [
          288,
          3824,
          178,
          11
        ]
      },
      {
        "index": 375,
        "before": [
          992,
          3312,
          176,
          11
        ],
        "after": [
          288,
          3728,
          176,
          11
        ]
      },
      {
        "index": 379,
        "before": [
          1056,
          3344,
          177,
          11
        ],
        "after": [
          512,
          3920,
          177,
          11
        ]
      },
      {
        "index": 412,
        "before": [
          4160,
          1680,
          131,
          3
        ],
        "after": [
          4160,
          1776,
          131,
          3
        ]
      }
    ],
    "groups": [
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 388,
          "center": [
            4224,
            272
          ],
          "depot_type": 131,
          "owner": 3,
          "top_left_tile": [
            130,
            7
          ]
        },
        "mineral_indices": [
          25,
          20,
          36,
          32,
          37,
          31,
          39,
          27,
          22,
          43,
          28
        ],
        "gas_indices": [
          0
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 1
        },
        "parent_site_index": 0,
        "group_index": 0,
        "group_sizes": [
          11
        ],
        "source_anchor": [
          4224,
          272
        ],
        "planned_depot_sites": [],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 434,
          "center": [
            4480,
            3632
          ],
          "depot_type": 131,
          "owner": 3,
          "top_left_tile": [
            138,
            112
          ]
        },
        "mineral_indices": [
          367,
          356,
          374,
          355,
          352,
          362,
          366,
          368,
          373,
          369,
          381
        ],
        "gas_indices": [
          311
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 363
        },
        "parent_site_index": 1,
        "group_index": 0,
        "group_sizes": [
          11
        ],
        "source_anchor": [
          4480,
          3632
        ],
        "planned_depot_sites": [],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "skipped_arc_slots": 2,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 414,
          "center": [
            5792,
            1744
          ],
          "depot_type": 131,
          "owner": 3,
          "top_left_tile": [
            179,
            53
          ]
        },
        "mineral_indices": [
          183,
          181,
          184,
          164,
          154,
          172,
          146,
          171,
          177,
          189
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 1
        },
        "parent_site_index": 2,
        "group_index": 0,
        "group_sizes": [
          10
        ],
        "source_anchor": [
          5792,
          1744
        ],
        "planned_depot_sites": [],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 400,
          "center": [
            768,
            592
          ],
          "depot_type": 133,
          "owner": 4,
          "top_left_tile": [
            22,
            17
          ]
        },
        "mineral_indices": [
          81,
          65,
          76,
          75,
          66,
          72,
          78,
          63,
          79
        ],
        "gas_indices": [
          68
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 926,
          "gas_exit": 2
        },
        "parent_site_index": 3,
        "group_index": 0,
        "group_sizes": [
          9
        ],
        "source_anchor": [
          768,
          592
        ],
        "planned_depot_sites": [],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 440,
          "center": [
            480,
            3760
          ],
          "depot_type": 133,
          "owner": 5,
          "top_left_tile": [
            13,
            116
          ]
        },
        "mineral_indices": [
          363,
          371,
          346,
          347,
          353,
          375,
          379,
          370
        ],
        "gas_indices": [
          351
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 24,
          "geometry": 97
        },
        "parent_site_index": 4,
        "group_index": 0,
        "group_sizes": [
          8
        ],
        "source_anchor": [
          480,
          3760
        ],
        "planned_depot_sites": [],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "maximum_minerals": 12,
        "placement_policy": "reviewed_playtest_layout"
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 408,
          "center": [
            4160,
            1424
          ],
          "depot_type": 132,
          "owner": 3,
          "top_left_tile": [
            128,
            43
          ]
        },
        "mineral_indices": [
          107,
          110,
          113,
          101,
          99,
          104,
          97
        ],
        "gas_indices": [
          111,
          487
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "resource_overlap": 6
        },
        "parent_site_index": 5,
        "group_index": 0,
        "group_sizes": [
          7
        ],
        "source_anchor": [
          4160,
          1424
        ],
        "planned_depot_sites": [],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 185,
          "center": [
            288,
            2032
          ],
          "depot_type": 106,
          "owner": 6,
          "top_left_tile": [
            7,
            62
          ]
        },
        "mineral_indices": [
          205,
          211,
          193,
          195,
          213,
          198
        ],
        "gas_indices": [
          199
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 4,
          "geometry": 6
        },
        "parent_site_index": 6,
        "group_index": 0,
        "group_sizes": [
          6
        ],
        "source_anchor": [
          288,
          2032
        ],
        "planned_depot_sites": [],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 420,
          "center": [
            5568,
            2768
          ],
          "depot_type": 131,
          "owner": 3,
          "top_left_tile": [
            172,
            85
          ]
        },
        "mineral_indices": [
          282,
          284,
          279,
          276,
          280,
          273
        ],
        "gas_indices": [
          261
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 1
        },
        "parent_site_index": 7,
        "group_index": 0,
        "group_sizes": [
          6
        ],
        "source_anchor": [
          5568,
          2768
        ],
        "planned_depot_sites": [],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      }
    ],
    "wave_cell_changes": [
      {
        "index": 1,
        "before": {
          "mission_id": 606,
          "owner": 5,
          "race": 0,
          "unit1": 43,
          "unit2": 44,
          "cell_count": 12,
          "center": [
            608,
            3952
          ],
          "target": [
            4164,
            1428
          ],
          "cells": [
            [
              532,
              3924
            ],
            [
              564,
              4020
            ],
            [
              596,
              4052
            ],
            [
              660,
              4052
            ],
            [
              500,
              3892
            ],
            [
              532,
              4052
            ],
            [
              500,
              4020
            ],
            [
              468,
              3956
            ],
            [
              724,
              4052
            ],
            [
              468,
              4052
            ],
            [
              436,
              3988
            ],
            [
              788,
              3796
            ]
          ],
          "source_unit": 131,
          "ground_route_connected": false,
          "flying_only": true,
          "source_is_original_hostile_position": true,
          "friendly_clearance_pixels": 512,
          "original_occupancy_clearance_pixels": [
            40,
            80
          ]
        },
        "after": {
          "mission_id": 606,
          "owner": 5,
          "race": 0,
          "unit1": 43,
          "unit2": 44,
          "cell_count": 12,
          "center": [
            608,
            3952
          ],
          "target": [
            4164,
            1428
          ],
          "cells": [
            [
              564,
              4020
            ],
            [
              596,
              4052
            ],
            [
              660,
              4052
            ],
            [
              532,
              4052
            ],
            [
              500,
              4020
            ],
            [
              724,
              4052
            ],
            [
              436,
              3988
            ],
            [
              308,
              3956
            ],
            [
              916,
              4052
            ],
            [
              276,
              3924
            ],
            [
              948,
              3988
            ],
            [
              244,
              3956
            ]
          ],
          "source_unit": 131,
          "ground_route_connected": false,
          "flying_only": true,
          "source_is_original_hostile_position": true,
          "friendly_clearance_pixels": 512,
          "original_occupancy_clearance_pixels": [
            40,
            80
          ]
        }
      }
    ]
  },
  "607": {
    "input_unit_sha256": "6f425e98c3da560d07fff329e9a40797b6ec4762cb42bc8244e89f36d65fec34",
    "moves": [
      {
        "index": 286,
        "before": [
          3136,
          3440,
          178,
          11
        ],
        "after": [
          3392,
          3504,
          178,
          11
        ]
      },
      {
        "index": 287,
        "before": [
          3200,
          3440,
          176,
          11
        ],
        "after": [
          3392,
          3472,
          176,
          11
        ]
      },
      {
        "index": 292,
        "before": [
          3264,
          3440,
          177,
          11
        ],
        "after": [
          3520,
          3696,
          177,
          11
        ]
      },
      {
        "index": 299,
        "before": [
          3776,
          3600,
          178,
          11
        ],
        "after": [
          3776,
          3568,
          178,
          11
        ]
      },
      {
        "index": 302,
        "before": [
          3072,
          3504,
          176,
          11
        ],
        "after": [
          3392,
          3600,
          176,
          11
        ]
      },
      {
        "index": 303,
        "before": [
          3776,
          3632,
          177,
          11
        ],
        "after": [
          3776,
          3600,
          177,
          11
        ]
      },
      {
        "index": 305,
        "before": [
          704,
          3504,
          177,
          11
        ],
        "after": [
          352,
          3632,
          177,
          11
        ]
      },
      {
        "index": 306,
        "before": [
          3072,
          3536,
          178,
          11
        ],
        "after": [
          3392,
          3632,
          178,
          11
        ]
      },
      {
        "index": 307,
        "before": [
          3360,
          3424,
          188,
          11
        ],
        "after": [
          3904,
          3456,
          188,
          11
        ]
      },
      {
        "index": 310,
        "before": [
          320,
          3888,
          178,
          11
        ],
        "after": [
          256,
          3760,
          178,
          11
        ]
      },
      {
        "index": 311,
        "before": [
          3776,
          3664,
          177,
          11
        ],
        "after": [
          3776,
          3632,
          177,
          11
        ]
      },
      {
        "index": 312,
        "before": [
          320,
          3856,
          176,
          11
        ],
        "after": [
          288,
          3696,
          176,
          11
        ]
      },
      {
        "index": 316,
        "before": [
          3072,
          3600,
          176,
          11
        ],
        "after": [
          3456,
          3696,
          176,
          11
        ]
      },
      {
        "index": 317,
        "before": [
          3072,
          3568,
          178,
          11
        ],
        "after": [
          3392,
          3664,
          178,
          11
        ]
      },
      {
        "index": 318,
        "before": [
          448,
          3984,
          176,
          11
        ],
        "after": [
          256,
          3856,
          176,
          11
        ]
      },
      {
        "index": 321,
        "before": [
          512,
          3984,
          177,
          11
        ],
        "after": [
          288,
          3920,
          177,
          11
        ]
      },
      {
        "index": 323,
        "before": [
          320,
          3920,
          177,
          11
        ],
        "after": [
          256,
          3792,
          177,
          11
        ]
      },
      {
        "index": 324,
        "before": [
          3712,
          3696,
          178,
          11
        ],
        "after": [
          3776,
          3664,
          178,
          11
        ]
      },
      {
        "index": 325,
        "before": [
          3584,
          3696,
          177,
          11
        ],
        "after": [
          3648,
          3696,
          177,
          11
        ]
      },
      {
        "index": 327,
        "before": [
          3520,
          3696,
          176,
          11
        ],
        "after": [
          3584,
          3696,
          176,
          11
        ]
      },
      {
        "index": 329,
        "before": [
          320,
          3952,
          177,
          11
        ],
        "after": [
          256,
          3824,
          177,
          11
        ]
      },
      {
        "index": 332,
        "before": [
          3648,
          3696,
          178,
          11
        ],
        "after": [
          3712,
          3696,
          178,
          11
        ]
      },
      {
        "index": 335,
        "before": [
          704,
          3536,
          177,
          11
        ],
        "after": [
          288,
          3632,
          177,
          11
        ]
      },
      {
        "index": 336,
        "before": [
          704,
          3568,
          176,
          11
        ],
        "after": [
          320,
          3664,
          176,
          11
        ]
      },
      {
        "index": 340,
        "before": [
          704,
          3600,
          178,
          11
        ],
        "after": [
          288,
          3728,
          178,
          11
        ]
      },
      {
        "index": 342,
        "before": [
          384,
          3984,
          178,
          11
        ],
        "after": [
          256,
          3888,
          178,
          11
        ]
      },
      {
        "index": 343,
        "before": [
          416,
          3648,
          157,
          5
        ],
        "after": [
          576,
          3648,
          157,
          5
        ]
      },
      {
        "index": 345,
        "before": [
          768,
          3472,
          176,
          11
        ],
        "after": [
          416,
          3632,
          176,
          11
        ]
      },
      {
        "index": 346,
        "before": [
          704,
          3632,
          177,
          11
        ],
        "after": [
          320,
          3984,
          177,
          11
        ]
      },
      {
        "index": 347,
        "before": [
          704,
          3664,
          178,
          11
        ],
        "after": [
          288,
          3952,
          178,
          11
        ]
      },
      {
        "index": 348,
        "before": [
          3872,
          3488,
          188,
          11
        ],
        "after": [
          3872,
          3392,
          188,
          11
        ]
      },
      {
        "index": 349,
        "before": [
          3664,
          3232,
          135,
          3
        ],
        "after": [
          3920,
          3584,
          135,
          3
        ]
      },
      {
        "index": 350,
        "before": [
          3488,
          3232,
          143,
          3
        ],
        "after": [
          3296,
          3296,
          143,
          3
        ]
      },
      {
        "index": 353,
        "before": [
          3360,
          3488,
          143,
          3
        ],
        "after": [
          3264,
          3168,
          143,
          3
        ]
      }
    ],
    "groups": [
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 328,
          "center": [
            512,
            3824
          ],
          "depot_type": 154,
          "owner": 5,
          "top_left_tile": [
            14,
            118
          ]
        },
        "mineral_indices": [
          312,
          318,
          310,
          321,
          329,
          323,
          342,
          345,
          305,
          335,
          336,
          340,
          346,
          347
        ],
        "gas_indices": [
          343
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 10
        },
        "parent_site_index": 0,
        "group_index": 0,
        "group_sizes": [
          14
        ],
        "source_anchor": [
          512,
          3824
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              1216,
              2096
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              36,
              64
            ]
          }
        ],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "maximum_minerals": 14,
        "placement_policy": "reviewed_playtest_layout"
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 354,
          "center": [
            3584,
            3536
          ],
          "depot_type": 131,
          "owner": 3,
          "top_left_tile": [
            110,
            109
          ]
        },
        "mineral_indices": [
          324,
          325,
          311,
          327,
          303,
          332,
          299,
          316,
          306,
          317,
          302,
          287,
          292,
          286
        ],
        "gas_indices": [
          307
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 1,
          "resource_overlap": 1
        },
        "parent_site_index": 1,
        "group_index": 0,
        "group_sizes": [
          14
        ],
        "source_anchor": [
          3584,
          3536
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              1216,
              2096
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              36,
              64
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "maximum_minerals": 14,
        "placement_policy": "reviewed_playtest_layout"
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            1216,
            2096
          ],
          "depot_type": 131,
          "owner": null,
          "top_left_tile": [
            36,
            64
          ]
        },
        "mineral_indices": [
          234,
          232,
          235,
          241,
          237,
          233,
          236,
          230,
          231
        ],
        "gas_indices": [
          242
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "gas_lane": 189,
          "plateau": 41,
          "gas_exit": 45,
          "gas_inside_bank": 4
        },
        "parent_site_index": 2,
        "group_index": 0,
        "group_sizes": [
          9
        ],
        "source_anchor": [
          1216,
          2096
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              1216,
              2096
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              36,
              64
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 352,
          "center": [
            3648,
            3376
          ],
          "depot_type": 131,
          "owner": 3,
          "top_left_tile": [
            112,
            104
          ]
        },
        "mineral_indices": [
          263,
          265,
          267,
          268,
          264,
          261,
          258,
          260,
          259
        ],
        "gas_indices": [
          348
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 18,
          "geometry": 28,
          "depot_clearance": 18,
          "army_route": 5
        },
        "parent_site_index": 3,
        "group_index": 0,
        "group_sizes": [
          9
        ],
        "source_anchor": [
          3648,
          3376
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              1216,
              2096
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              36,
              64
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 139,
          "center": [
            2048,
            1456
          ],
          "depot_type": 154,
          "owner": 1,
          "top_left_tile": [
            62,
            44
          ]
        },
        "mineral_indices": [
          173,
          172,
          179,
          186,
          194,
          187,
          190,
          191
        ],
        "gas_indices": [
          193
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 36
        },
        "parent_site_index": 4,
        "group_index": 0,
        "group_sizes": [
          8
        ],
        "source_anchor": [
          2048,
          1456
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              1216,
              2096
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              36,
              64
            ]
          }
        ],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      }
    ]
  },
  "608": {
    "input_unit_sha256": "db70e81ea85fa879d4dbedfeae1288cf178e5a46696ab7ab5ffc525b1d22e391",
    "moves": [
      {
        "index": 0,
        "before": [
          5344,
          528,
          178,
          11
        ],
        "after": [
          5920,
          272,
          178,
          11
        ]
      },
      {
        "index": 1,
        "before": [
          5824,
          144,
          177,
          11
        ],
        "after": [
          5440,
          112,
          177,
          11
        ]
      },
      {
        "index": 2,
        "before": [
          5344,
          496,
          178,
          11
        ],
        "after": [
          5952,
          240,
          178,
          11
        ]
      },
      {
        "index": 4,
        "before": [
          5920,
          208,
          177,
          11
        ],
        "after": [
          5632,
          80,
          177,
          11
        ]
      },
      {
        "index": 5,
        "before": [
          5472,
          464,
          178,
          11
        ],
        "after": [
          5952,
          208,
          178,
          11
        ]
      },
      {
        "index": 6,
        "before": [
          5888,
          144,
          178,
          11
        ],
        "after": [
          5568,
          112,
          178,
          11
        ]
      },
      {
        "index": 7,
        "before": [
          5920,
          240,
          178,
          11
        ],
        "after": [
          5696,
          80,
          178,
          11
        ]
      },
      {
        "index": 12,
        "before": [
          5344,
          560,
          177,
          11
        ],
        "after": [
          5920,
          304,
          177,
          11
        ]
      },
      {
        "index": 13,
        "before": [
          5664,
          128,
          110,
          6
        ],
        "after": [
          5728,
          480,
          110,
          6
        ]
      },
      {
        "index": 16,
        "before": [
          5408,
          464,
          178,
          11
        ],
        "after": [
          5856,
          144,
          178,
          11
        ]
      },
      {
        "index": 20,
        "before": [
          5920,
          272,
          177,
          11
        ],
        "after": [
          5792,
          112,
          177,
          11
        ]
      },
      {
        "index": 25,
        "before": [
          5344,
          592,
          178,
          11
        ],
        "after": [
          5504,
          112,
          178,
          11
        ]
      },
      {
        "index": 26,
        "before": [
          5920,
          304,
          177,
          11
        ],
        "after": [
          5920,
          144,
          177,
          11
        ]
      },
      {
        "index": 34,
        "before": [
          5344,
          624,
          176,
          11
        ],
        "after": [
          5504,
          208,
          176,
          11
        ]
      },
      {
        "index": 78,
        "before": [
          2848,
          512,
          149,
          7
        ],
        "after": [
          2976,
          512,
          149,
          7
        ]
      },
      {
        "index": 80,
        "before": [
          2208,
          1296,
          178,
          11
        ],
        "after": [
          2528,
          624,
          178,
          11
        ]
      },
      {
        "index": 88,
        "before": [
          2208,
          1360,
          177,
          11
        ],
        "after": [
          2560,
          816,
          177,
          11
        ]
      },
      {
        "index": 89,
        "before": [
          2592,
          816,
          178,
          11
        ],
        "after": [
          2560,
          528,
          178,
          11
        ]
      },
      {
        "index": 92,
        "before": [
          2208,
          1392,
          176,
          11
        ],
        "after": [
          2592,
          848,
          176,
          11
        ]
      },
      {
        "index": 98,
        "before": [
          2272,
          1232,
          177,
          11
        ],
        "after": [
          2656,
          880,
          177,
          11
        ]
      },
      {
        "index": 101,
        "before": [
          2208,
          1328,
          177,
          11
        ],
        "after": [
          2528,
          720,
          177,
          11
        ]
      },
      {
        "index": 103,
        "before": [
          2848,
          880,
          178,
          11
        ],
        "after": [
          2816,
          464,
          178,
          11
        ]
      },
      {
        "index": 104,
        "before": [
          2720,
          848,
          178,
          11
        ],
        "after": [
          2752,
          464,
          178,
          11
        ]
      },
      {
        "index": 105,
        "before": [
          2784,
          848,
          178,
          11
        ],
        "after": [
          2720,
          912,
          178,
          11
        ]
      },
      {
        "index": 111,
        "before": [
          2208,
          1424,
          177,
          11
        ],
        "after": [
          2592,
          880,
          177,
          11
        ]
      },
      {
        "index": 116,
        "before": [
          2208,
          1264,
          178,
          11
        ],
        "after": [
          2560,
          560,
          178,
          11
        ]
      },
      {
        "index": 119,
        "before": [
          2560,
          720,
          177,
          11
        ],
        "after": [
          2560,
          496,
          177,
          11
        ]
      },
      {
        "index": 125,
        "before": [
          2656,
          848,
          177,
          11
        ],
        "after": [
          2688,
          496,
          177,
          11
        ]
      },
      {
        "index": 536,
        "before": [
          1232,
          2016,
          142,
          3
        ],
        "after": [
          1232,
          1856,
          142,
          3
        ]
      }
    ],
    "groups": [
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 519,
          "center": [
            4608,
            1552
          ],
          "depot_type": 133,
          "owner": 4,
          "top_left_tile": [
            142,
            47
          ]
        },
        "mineral_indices": [
          357,
          376,
          348,
          381,
          374,
          347,
          350,
          343,
          363,
          370
        ],
        "gas_indices": [
          306,
          377
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 54,
          "resource_overlap": 3,
          "gas_exit": 1
        },
        "parent_site_index": 0,
        "group_index": 0,
        "group_sizes": [
          10,
          11
        ],
        "source_anchor": [
          4608,
          1552
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              4928,
              1872
            ],
            "depot_type": 133,
            "owner": 4,
            "top_left_tile": [
              152,
              57
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              5792,
              2736
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              179,
              84
            ]
          },
          {
            "kind": "expansion",
            "center": [
              5472,
              2736
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              169,
              84
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              3296,
              2704
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              101,
              83
            ]
          },
          {
            "kind": "expansion",
            "center": [
              288,
              1872
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              7,
              57
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            4928,
            1872
          ],
          "depot_type": 133,
          "owner": 4,
          "top_left_tile": [
            152,
            57
          ],
          "additional_group_depot": true
        },
        "mineral_indices": [
          375,
          382,
          383,
          320,
          332,
          342,
          339,
          336,
          328,
          319,
          317
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 4,
          "plateau": 9
        },
        "parent_site_index": 0,
        "group_index": 1,
        "group_sizes": [
          10,
          11
        ],
        "source_anchor": [
          4608,
          1552
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              4928,
              1872
            ],
            "depot_type": 133,
            "owner": 4,
            "top_left_tile": [
              152,
              57
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              5792,
              2736
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              179,
              84
            ]
          },
          {
            "kind": "expansion",
            "center": [
              5472,
              2736
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              169,
              84
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              3296,
              2704
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              101,
              83
            ]
          },
          {
            "kind": "expansion",
            "center": [
              288,
              1872
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              7,
              57
            ]
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            5792,
            2736
          ],
          "depot_type": 131,
          "owner": null,
          "top_left_tile": [
            179,
            84
          ]
        },
        "mineral_indices": [
          457,
          456,
          466,
          468,
          464,
          467,
          474,
          478
        ],
        "gas_indices": [
          459
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 1
        },
        "parent_site_index": 1,
        "group_index": 0,
        "group_sizes": [
          8,
          9
        ],
        "source_anchor": [
          5792,
          2736
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              4928,
              1872
            ],
            "depot_type": 133,
            "owner": 4,
            "top_left_tile": [
              152,
              57
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              5792,
              2736
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              179,
              84
            ]
          },
          {
            "kind": "expansion",
            "center": [
              5472,
              2736
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              169,
              84
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              3296,
              2704
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              101,
              83
            ]
          },
          {
            "kind": "expansion",
            "center": [
              288,
              1872
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              7,
              57
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            5472,
            2736
          ],
          "depot_type": 131,
          "owner": null,
          "top_left_tile": [
            169,
            84
          ],
          "additional_group_depot": true
        },
        "mineral_indices": [
          453,
          458,
          462,
          460,
          461,
          477,
          463,
          473,
          465
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 1,
          "depot_clearance": 1
        },
        "parent_site_index": 1,
        "group_index": 1,
        "group_sizes": [
          8,
          9
        ],
        "source_anchor": [
          5792,
          2736
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              4928,
              1872
            ],
            "depot_type": 133,
            "owner": 4,
            "top_left_tile": [
              152,
              57
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              5792,
              2736
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              179,
              84
            ]
          },
          {
            "kind": "expansion",
            "center": [
              5472,
              2736
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              169,
              84
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              3296,
              2704
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              101,
              83
            ]
          },
          {
            "kind": "expansion",
            "center": [
              288,
              1872
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              7,
              57
            ]
          }
        ],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 43,
          "center": [
            5728,
            304
          ],
          "depot_type": 106,
          "owner": 6,
          "top_left_tile": [
            177,
            8
          ]
        },
        "mineral_indices": [
          19,
          20,
          7,
          6,
          26,
          4,
          1,
          34,
          25,
          12,
          0,
          2,
          5,
          16
        ],
        "gas_indices": [
          13
        ],
        "status": "ladder_separate_gas",
        "reasons": {},
        "parent_site_index": 2,
        "group_index": 0,
        "group_sizes": [
          14
        ],
        "source_anchor": [
          5728,
          304
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              4928,
              1872
            ],
            "depot_type": 133,
            "owner": 4,
            "top_left_tile": [
              152,
              57
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              5792,
              2736
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              179,
              84
            ]
          },
          {
            "kind": "expansion",
            "center": [
              5472,
              2736
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              169,
              84
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              3296,
              2704
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              101,
              83
            ]
          },
          {
            "kind": "expansion",
            "center": [
              288,
              1872
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              7,
              57
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "maximum_minerals": 14,
        "placement_policy": "reviewed_playtest_layout"
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 501,
          "center": [
            2784,
            688
          ],
          "depot_type": 133,
          "owner": 7,
          "top_left_tile": [
            85,
            20
          ]
        },
        "mineral_indices": [
          103,
          89,
          125,
          105,
          119,
          104,
          111,
          92,
          88,
          101,
          116,
          80,
          98
        ],
        "gas_indices": [
          78
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 28
        },
        "parent_site_index": 3,
        "group_index": 0,
        "group_sizes": [
          13
        ],
        "source_anchor": [
          2784,
          688
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              4928,
              1872
            ],
            "depot_type": 133,
            "owner": 4,
            "top_left_tile": [
              152,
              57
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              5792,
              2736
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              179,
              84
            ]
          },
          {
            "kind": "expansion",
            "center": [
              5472,
              2736
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              169,
              84
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              3296,
              2704
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              101,
              83
            ]
          },
          {
            "kind": "expansion",
            "center": [
              288,
              1872
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              7,
              57
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "maximum_minerals": 13,
        "placement_policy": "reviewed_playtest_layout"
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 106,
          "center": [
            768,
            496
          ],
          "depot_type": 106,
          "owner": 6,
          "top_left_tile": [
            22,
            14
          ]
        },
        "mineral_indices": [
          115,
          41,
          102,
          160,
          77,
          146,
          76,
          129,
          55,
          128,
          50,
          62
        ],
        "gas_indices": [
          51
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 58,
          "gas_inside_bank": 5
        },
        "parent_site_index": 4,
        "group_index": 0,
        "group_sizes": [
          12
        ],
        "source_anchor": [
          768,
          496
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              4928,
              1872
            ],
            "depot_type": 133,
            "owner": 4,
            "top_left_tile": [
              152,
              57
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              5792,
              2736
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              179,
              84
            ]
          },
          {
            "kind": "expansion",
            "center": [
              5472,
              2736
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              169,
              84
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              3296,
              2704
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              101,
              83
            ]
          },
          {
            "kind": "expansion",
            "center": [
              288,
              1872
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              7,
              57
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            3296,
            2704
          ],
          "depot_type": 131,
          "owner": null,
          "top_left_tile": [
            101,
            83
          ]
        },
        "mineral_indices": [
          483,
          484,
          487,
          490,
          489,
          491,
          488,
          492,
          485,
          486,
          493
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {},
        "parent_site_index": 5,
        "group_index": 0,
        "group_sizes": [
          11
        ],
        "source_anchor": [
          3296,
          2704
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              4928,
              1872
            ],
            "depot_type": 133,
            "owner": 4,
            "top_left_tile": [
              152,
              57
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              5792,
              2736
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              179,
              84
            ]
          },
          {
            "kind": "expansion",
            "center": [
              5472,
              2736
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              169,
              84
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              3296,
              2704
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              101,
              83
            ]
          },
          {
            "kind": "expansion",
            "center": [
              288,
              1872
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              7,
              57
            ]
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 535,
          "center": [
            2336,
            1968
          ],
          "depot_type": 131,
          "owner": 4,
          "top_left_tile": [
            71,
            60
          ]
        },
        "mineral_indices": [
          421,
          411,
          423,
          431,
          429,
          435,
          424,
          436,
          415,
          428
        ],
        "gas_indices": [
          389
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 1,
          "gas_exit": 2
        },
        "parent_site_index": 6,
        "group_index": 0,
        "group_sizes": [
          10
        ],
        "source_anchor": [
          2336,
          1968
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              4928,
              1872
            ],
            "depot_type": 133,
            "owner": 4,
            "top_left_tile": [
              152,
              57
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              5792,
              2736
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              179,
              84
            ]
          },
          {
            "kind": "expansion",
            "center": [
              5472,
              2736
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              169,
              84
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              3296,
              2704
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              101,
              83
            ]
          },
          {
            "kind": "expansion",
            "center": [
              288,
              1872
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              7,
              57
            ]
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 538,
          "center": [
            1216,
            2128
          ],
          "depot_type": 132,
          "owner": 3,
          "top_left_tile": [
            36,
            65
          ]
        },
        "mineral_indices": [
          454,
          446,
          439,
          425,
          430,
          451,
          440,
          442
        ],
        "gas_indices": [
          412,
          581
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "resource_overlap": 7
        },
        "parent_site_index": 7,
        "group_index": 0,
        "group_sizes": [
          8
        ],
        "source_anchor": [
          1216,
          2128
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              4928,
              1872
            ],
            "depot_type": 133,
            "owner": 4,
            "top_left_tile": [
              152,
              57
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              5792,
              2736
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              179,
              84
            ]
          },
          {
            "kind": "expansion",
            "center": [
              5472,
              2736
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              169,
              84
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              3296,
              2704
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              101,
              83
            ]
          },
          {
            "kind": "expansion",
            "center": [
              288,
              1872
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              7,
              57
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            288,
            1872
          ],
          "depot_type": 131,
          "owner": null,
          "top_left_tile": [
            7,
            57
          ]
        },
        "mineral_indices": [
          355,
          361,
          362
        ],
        "gas_indices": [
          356
        ],
        "status": "ladder_separate_gas",
        "reasons": {},
        "parent_site_index": 8,
        "group_index": 0,
        "group_sizes": [
          3
        ],
        "source_anchor": [
          288,
          1872
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              4928,
              1872
            ],
            "depot_type": 133,
            "owner": 4,
            "top_left_tile": [
              152,
              57
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              5792,
              2736
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              179,
              84
            ]
          },
          {
            "kind": "expansion",
            "center": [
              5472,
              2736
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              169,
              84
            ],
            "additional_group_depot": true
          },
          {
            "kind": "expansion",
            "center": [
              3296,
              2704
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              101,
              83
            ]
          },
          {
            "kind": "expansion",
            "center": [
              288,
              1872
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              7,
              57
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      }
    ]
  },
  "609": {
    "input_unit_sha256": "52b7c368802777d4ae294261c5ee81669ff42b904e017f270bb424b5f200e27e",
    "moves": [
      {
        "index": 97,
        "before": [
          2496,
          1840,
          176,
          11
        ],
        "after": [
          2880,
          1424,
          176,
          11
        ]
      },
      {
        "index": 107,
        "before": [
          2496,
          1872,
          177,
          11
        ],
        "after": [
          2880,
          1456,
          177,
          11
        ]
      },
      {
        "index": 113,
        "before": [
          2496,
          1904,
          176,
          11
        ],
        "after": [
          2880,
          1488,
          176,
          11
        ]
      },
      {
        "index": 120,
        "before": [
          2496,
          1808,
          177,
          11
        ],
        "after": [
          2880,
          1392,
          177,
          11
        ]
      },
      {
        "index": 122,
        "before": [
          2880,
          1424,
          177,
          11
        ],
        "after": [
          2880,
          1264,
          177,
          11
        ]
      },
      {
        "index": 123,
        "before": [
          2880,
          1392,
          176,
          11
        ],
        "after": [
          2912,
          1232,
          176,
          11
        ]
      },
      {
        "index": 124,
        "before": [
          3296,
          1344,
          157,
          1
        ],
        "after": [
          3168,
          1632,
          157,
          1
        ]
      },
      {
        "index": 133,
        "before": [
          2880,
          1456,
          178,
          11
        ],
        "after": [
          2880,
          1296,
          178,
          11
        ]
      },
      {
        "index": 140,
        "before": [
          2592,
          1936,
          176,
          11
        ],
        "after": [
          2976,
          1552,
          176,
          11
        ]
      },
      {
        "index": 150,
        "before": [
          2528,
          1936,
          177,
          11
        ],
        "after": [
          2912,
          1552,
          177,
          11
        ]
      },
      {
        "index": 151,
        "before": [
          2880,
          1488,
          178,
          11
        ],
        "after": [
          2880,
          1328,
          178,
          11
        ]
      },
      {
        "index": 157,
        "before": [
          2912,
          1552,
          177,
          11
        ],
        "after": [
          2880,
          1360,
          177,
          11
        ]
      },
      {
        "index": 161,
        "before": [
          2976,
          1552,
          178,
          11
        ],
        "after": [
          2976,
          1232,
          178,
          11
        ]
      },
      {
        "index": 274,
        "before": [
          928,
          1424,
          131,
          3
        ],
        "after": [
          992,
          1328,
          131,
          3
        ]
      }
    ],
    "groups": [
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 131,
          "center": [
            3072,
            1392
          ],
          "depot_type": 154,
          "owner": 1,
          "top_left_tile": [
            94,
            42
          ]
        },
        "mineral_indices": [
          133,
          151,
          122,
          123,
          161,
          157,
          120,
          150,
          140,
          113,
          107,
          97
        ],
        "gas_indices": [
          124
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 6,
          "geometry": 16
        },
        "parent_site_index": 0,
        "group_index": 0,
        "group_sizes": [
          12
        ],
        "source_anchor": [
          3072,
          1392
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              96,
              2384
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              1,
              73
            ]
          }
        ],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "maximum_minerals": 12,
        "placement_policy": "reviewed_playtest_layout"
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 272,
          "center": [
            672,
            1360
          ],
          "depot_type": 133,
          "owner": 3,
          "top_left_tile": [
            19,
            41
          ]
        },
        "mineral_indices": [
          90,
          94,
          89,
          115,
          103,
          86,
          87,
          95,
          91,
          93,
          88
        ],
        "gas_indices": [
          130,
          325
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 23,
          "resource_overlap": 1,
          "gas_exit": 2
        },
        "parent_site_index": 1,
        "group_index": 0,
        "group_sizes": [
          11
        ],
        "source_anchor": [
          672,
          1360
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              96,
              2384
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              1,
              73
            ]
          }
        ],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 36,
          "center": [
            480,
            336
          ],
          "depot_type": 106,
          "owner": 6,
          "top_left_tile": [
            13,
            9
          ]
        },
        "mineral_indices": [
          13,
          14,
          16,
          8,
          12,
          7,
          15
        ],
        "gas_indices": [
          33
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 479
        },
        "parent_site_index": 2,
        "group_index": 0,
        "group_sizes": [
          7
        ],
        "source_anchor": [
          480,
          336
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              96,
              2384
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              1,
              73
            ]
          }
        ],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            96,
            2384
          ],
          "depot_type": 131,
          "owner": null,
          "top_left_tile": [
            1,
            73
          ]
        },
        "mineral_indices": [
          251,
          246,
          260,
          240,
          255,
          248,
          261
        ],
        "gas_indices": [
          263
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 180,
          "plateau": 340
        },
        "parent_site_index": 3,
        "group_index": 0,
        "group_sizes": [
          7
        ],
        "source_anchor": [
          96,
          2384
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              96,
              2384
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              1,
              73
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      }
    ],
    "wave_cell_changes": [
      {
        "index": 2,
        "before": {
          "mission_id": 609,
          "owner": 1,
          "race": 2,
          "unit1": 65,
          "unit2": 66,
          "cell_count": 17,
          "center": [
            3104,
            1248
          ],
          "target": [
            676,
            1364
          ],
          "cells": [
            [
              3156,
              1172
            ],
            [
              3028,
              1300
            ],
            [
              3188,
              1300
            ],
            [
              3156,
              1332
            ],
            [
              3092,
              1140
            ],
            [
              3124,
              1108
            ],
            [
              3060,
              1108
            ],
            [
              3252,
              1268
            ],
            [
              2996,
              1140
            ],
            [
              2964,
              1172
            ],
            [
              3188,
              1108
            ],
            [
              2932,
              1268
            ],
            [
              3028,
              1076
            ],
            [
              2964,
              1108
            ],
            [
              2932,
              1140
            ],
            [
              2996,
              1428
            ],
            [
              2932,
              1076
            ]
          ],
          "source_unit": 162,
          "ground_route_connected": true,
          "flying_only": false,
          "source_is_original_hostile_position": true,
          "friendly_clearance_pixels": 512,
          "original_occupancy_clearance_pixels": [
            40,
            80
          ]
        },
        "after": {
          "mission_id": 609,
          "owner": 1,
          "race": 2,
          "unit1": 65,
          "unit2": 66,
          "cell_count": 17,
          "center": [
            3104,
            1248
          ],
          "target": [
            676,
            1364
          ],
          "cells": [
            [
              3028,
              1300
            ],
            [
              3188,
              1300
            ],
            [
              3156,
              1332
            ],
            [
              3220,
              1332
            ],
            [
              3252,
              1300
            ],
            [
              3252,
              1364
            ],
            [
              3284,
              1332
            ],
            [
              3124,
              1460
            ],
            [
              3028,
              1460
            ],
            [
              3316,
              1364
            ],
            [
              3348,
              1332
            ],
            [
              3188,
              1524
            ],
            [
              3380,
              1364
            ],
            [
              3316,
              1620
            ],
            [
              3284,
              1652
            ],
            [
              3316,
              1684
            ],
            [
              2772,
              1748
            ]
          ],
          "source_unit": 162,
          "ground_route_connected": true,
          "flying_only": false,
          "source_is_original_hostile_position": true,
          "friendly_clearance_pixels": 512,
          "original_occupancy_clearance_pixels": [
            40,
            80
          ]
        }
      }
    ]
  },
  "610": {
    "input_unit_sha256": "d799bad564b8c6037d957019ee7cd2b14afe50110e64876ace767b72ad459800",
    "moves": [
      {
        "index": 0,
        "before": [
          5440,
          496,
          176,
          11
        ],
        "after": [
          5440,
          784,
          176,
          11
        ]
      },
      {
        "index": 3,
        "before": [
          5632,
          496,
          177,
          11
        ],
        "after": [
          5728,
          688,
          177,
          11
        ]
      },
      {
        "index": 5,
        "before": [
          5088,
          688,
          177,
          11
        ],
        "after": [
          5248,
          752,
          177,
          11
        ]
      },
      {
        "index": 8,
        "before": [
          5504,
          496,
          178,
          11
        ],
        "after": [
          5504,
          784,
          178,
          11
        ]
      },
      {
        "index": 9,
        "before": [
          5568,
          496,
          177,
          11
        ],
        "after": [
          5568,
          752,
          177,
          11
        ]
      },
      {
        "index": 10,
        "before": [
          5632,
          528,
          177,
          11
        ],
        "after": [
          5632,
          720,
          177,
          11
        ]
      },
      {
        "index": 13,
        "before": [
          5024,
          688,
          178,
          11
        ],
        "after": [
          5184,
          720,
          178,
          11
        ]
      },
      {
        "index": 14,
        "before": [
          4960,
          624,
          177,
          11
        ],
        "after": [
          5024,
          656,
          177,
          11
        ]
      },
      {
        "index": 15,
        "before": [
          5216,
          688,
          177,
          11
        ],
        "after": [
          5376,
          784,
          177,
          11
        ]
      },
      {
        "index": 23,
        "before": [
          5696,
          592,
          177,
          11
        ],
        "after": [
          5792,
          656,
          177,
          11
        ]
      },
      {
        "index": 34,
        "before": [
          5760,
          592,
          177,
          11
        ],
        "after": [
          5856,
          592,
          177,
          11
        ]
      },
      {
        "index": 35,
        "before": [
          5152,
          688,
          178,
          11
        ],
        "after": [
          5312,
          784,
          178,
          11
        ]
      },
      {
        "index": 41,
        "before": [
          4960,
          656,
          177,
          11
        ],
        "after": [
          5088,
          688,
          177,
          11
        ]
      },
      {
        "index": 659,
        "before": [
          2912,
          2960,
          131,
          3
        ],
        "after": [
          2880,
          3056,
          131,
          3
        ]
      },
      {
        "index": 669,
        "before": [
          3232,
          3152,
          131,
          3
        ],
        "after": [
          3392,
          3312,
          131,
          3
        ]
      }
    ],
    "groups": [
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 52,
          "center": [
            5408,
            336
          ],
          "depot_type": 106,
          "owner": 6,
          "top_left_tile": [
            167,
            9
          ]
        },
        "mineral_indices": [
          10,
          23,
          9,
          8,
          3,
          0,
          34,
          2,
          41,
          14,
          13,
          5,
          35,
          15
        ],
        "gas_indices": [
          58
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 51,
          "gas_exit": 6,
          "depot_clearance": 42,
          "plateau": 14
        },
        "parent_site_index": 0,
        "group_index": 0,
        "group_sizes": [
          14
        ],
        "source_anchor": [
          5408,
          336
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              2816,
              4080
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              86,
              126
            ]
          },
          {
            "kind": "expansion",
            "center": [
              544,
              304
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              15,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              256,
              5744
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              6,
              178
            ]
          },
          {
            "kind": "expansion",
            "center": [
              5472,
              5904
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              169,
              183
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3072,
              1328
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              94,
              40
            ]
          },
          {
            "kind": "expansion",
            "center": [
              5792,
              1840
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              179,
              56
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "maximum_minerals": 14,
        "placement_policy": "reviewed_playtest_layout"
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 276,
          "center": [
            448,
            2544
          ],
          "depot_type": 106,
          "owner": 0,
          "top_left_tile": [
            12,
            78
          ]
        },
        "mineral_indices": [
          285,
          293,
          305,
          310,
          292,
          280,
          301,
          302,
          296,
          286,
          304
        ],
        "gas_indices": [
          312
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 55,
          "army_route": 12
        },
        "parent_site_index": 1,
        "group_index": 0,
        "group_sizes": [
          11
        ],
        "source_anchor": [
          448,
          2544
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              2816,
              4080
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              86,
              126
            ]
          },
          {
            "kind": "expansion",
            "center": [
              544,
              304
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              15,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              256,
              5744
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              6,
              178
            ]
          },
          {
            "kind": "expansion",
            "center": [
              5472,
              5904
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              169,
              183
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3072,
              1328
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              94,
              40
            ]
          },
          {
            "kind": "expansion",
            "center": [
              5792,
              1840
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              179,
              56
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 663,
          "center": [
            3072,
            3056
          ],
          "depot_type": 133,
          "owner": 3,
          "top_left_tile": [
            94,
            94
          ]
        },
        "mineral_indices": [
          347,
          343,
          332,
          337,
          333,
          326,
          320,
          319,
          342,
          349
        ],
        "gas_indices": [
          358,
          742
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 54,
          "gas_inside_bank": 26
        },
        "parent_site_index": 2,
        "group_index": 0,
        "group_sizes": [
          10
        ],
        "source_anchor": [
          3072,
          3056
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              2816,
              4080
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              86,
              126
            ]
          },
          {
            "kind": "expansion",
            "center": [
              544,
              304
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              15,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              256,
              5744
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              6,
              178
            ]
          },
          {
            "kind": "expansion",
            "center": [
              5472,
              5904
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              169,
              183
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3072,
              1328
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              94,
              40
            ]
          },
          {
            "kind": "expansion",
            "center": [
              5792,
              1840
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              179,
              56
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            2816,
            4080
          ],
          "depot_type": 131,
          "owner": null,
          "top_left_tile": [
            86,
            126
          ]
        },
        "mineral_indices": [
          422,
          420,
          432,
          437,
          433,
          435,
          434,
          439,
          421,
          438
        ],
        "gas_indices": [
          446
        ],
        "status": "ladder_separate_gas",
        "reasons": {},
        "parent_site_index": 3,
        "group_index": 0,
        "group_sizes": [
          10
        ],
        "source_anchor": [
          2816,
          4080
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              2816,
              4080
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              86,
              126
            ]
          },
          {
            "kind": "expansion",
            "center": [
              544,
              304
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              15,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              256,
              5744
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              6,
              178
            ]
          },
          {
            "kind": "expansion",
            "center": [
              5472,
              5904
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              169,
              183
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3072,
              1328
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              94,
              40
            ]
          },
          {
            "kind": "expansion",
            "center": [
              5792,
              1840
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              179,
              56
            ]
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 615,
          "center": [
            3744,
            5424
          ],
          "depot_type": 154,
          "owner": 1,
          "top_left_tile": [
            115,
            168
          ]
        },
        "mineral_indices": [
          632,
          635,
          637,
          625,
          629,
          633,
          636,
          631,
          634,
          624
        ],
        "gas_indices": [
          616
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 21
        },
        "parent_site_index": 4,
        "group_index": 0,
        "group_sizes": [
          10
        ],
        "source_anchor": [
          3744,
          5424
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              2816,
              4080
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              86,
              126
            ]
          },
          {
            "kind": "expansion",
            "center": [
              544,
              304
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              15,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              256,
              5744
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              6,
              178
            ]
          },
          {
            "kind": "expansion",
            "center": [
              5472,
              5904
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              169,
              183
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3072,
              1328
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              94,
              40
            ]
          },
          {
            "kind": "expansion",
            "center": [
              5792,
              1840
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              179,
              56
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            544,
            304
          ],
          "depot_type": 131,
          "owner": null,
          "top_left_tile": [
            15,
            8
          ]
        },
        "mineral_indices": [
          37,
          25,
          36,
          17,
          16,
          20,
          11,
          24
        ],
        "gas_indices": [
          21
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 1
        },
        "parent_site_index": 5,
        "group_index": 0,
        "group_sizes": [
          8
        ],
        "source_anchor": [
          544,
          304
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              2816,
              4080
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              86,
              126
            ]
          },
          {
            "kind": "expansion",
            "center": [
              544,
              304
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              15,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              256,
              5744
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              6,
              178
            ]
          },
          {
            "kind": "expansion",
            "center": [
              5472,
              5904
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              169,
              183
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3072,
              1328
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              94,
              40
            ]
          },
          {
            "kind": "expansion",
            "center": [
              5792,
              1840
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              179,
              56
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 463,
          "center": [
            608,
            4240
          ],
          "depot_type": 106,
          "owner": 0,
          "top_left_tile": [
            17,
            131
          ]
        },
        "mineral_indices": [
          485,
          486,
          477,
          490,
          492,
          479,
          491,
          476
        ],
        "gas_indices": [
          468
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 5,
          "plateau": 3
        },
        "parent_site_index": 6,
        "group_index": 0,
        "group_sizes": [
          8
        ],
        "source_anchor": [
          608,
          4240
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              2816,
              4080
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              86,
              126
            ]
          },
          {
            "kind": "expansion",
            "center": [
              544,
              304
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              15,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              256,
              5744
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              6,
              178
            ]
          },
          {
            "kind": "expansion",
            "center": [
              5472,
              5904
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              169,
              183
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3072,
              1328
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              94,
              40
            ]
          },
          {
            "kind": "expansion",
            "center": [
              5792,
              1840
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              179,
              56
            ]
          }
        ],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 512,
          "center": [
            5600,
            4592
          ],
          "depot_type": 154,
          "owner": 1,
          "top_left_tile": [
            173,
            142
          ]
        },
        "mineral_indices": [
          478,
          482,
          495,
          511,
          518,
          487,
          500,
          506
        ],
        "gas_indices": [
          484
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 1,
          "geometry": 2
        },
        "parent_site_index": 7,
        "group_index": 0,
        "group_sizes": [
          8
        ],
        "source_anchor": [
          5600,
          4592
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              2816,
              4080
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              86,
              126
            ]
          },
          {
            "kind": "expansion",
            "center": [
              544,
              304
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              15,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              256,
              5744
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              6,
              178
            ]
          },
          {
            "kind": "expansion",
            "center": [
              5472,
              5904
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              169,
              183
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3072,
              1328
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              94,
              40
            ]
          },
          {
            "kind": "expansion",
            "center": [
              5792,
              1840
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              179,
              56
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            256,
            5744
          ],
          "depot_type": 131,
          "owner": null,
          "top_left_tile": [
            6,
            178
          ]
        },
        "mineral_indices": [
          647,
          650,
          639,
          641,
          646,
          642,
          649,
          645
        ],
        "gas_indices": [
          577
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 20,
          "gas_lane": 13,
          "gas_exit": 5
        },
        "parent_site_index": 8,
        "group_index": 0,
        "group_sizes": [
          8
        ],
        "source_anchor": [
          256,
          5744
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              2816,
              4080
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              86,
              126
            ]
          },
          {
            "kind": "expansion",
            "center": [
              544,
              304
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              15,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              256,
              5744
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              6,
              178
            ]
          },
          {
            "kind": "expansion",
            "center": [
              5472,
              5904
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              169,
              183
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3072,
              1328
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              94,
              40
            ]
          },
          {
            "kind": "expansion",
            "center": [
              5792,
              1840
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              179,
              56
            ]
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            5472,
            5904
          ],
          "depot_type": 131,
          "owner": null,
          "top_left_tile": [
            169,
            183
          ]
        },
        "mineral_indices": [
          651,
          643,
          644,
          648,
          653,
          652,
          654
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 25
        },
        "parent_site_index": 9,
        "group_index": 0,
        "group_sizes": [
          7
        ],
        "source_anchor": [
          5472,
          5904
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              2816,
              4080
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              86,
              126
            ]
          },
          {
            "kind": "expansion",
            "center": [
              544,
              304
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              15,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              256,
              5744
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              6,
              178
            ]
          },
          {
            "kind": "expansion",
            "center": [
              5472,
              5904
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              169,
              183
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3072,
              1328
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              94,
              40
            ]
          },
          {
            "kind": "expansion",
            "center": [
              5792,
              1840
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              179,
              56
            ]
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            3072,
            1328
          ],
          "depot_type": 131,
          "owner": null,
          "top_left_tile": [
            94,
            40
          ]
        },
        "mineral_indices": [
          190,
          192,
          191,
          195,
          198,
          199
        ],
        "gas_indices": [
          193
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 60,
          "depot_clearance": 9,
          "gas_exit": 4
        },
        "parent_site_index": 10,
        "group_index": 0,
        "group_sizes": [
          6
        ],
        "source_anchor": [
          3072,
          1328
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              2816,
              4080
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              86,
              126
            ]
          },
          {
            "kind": "expansion",
            "center": [
              544,
              304
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              15,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              256,
              5744
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              6,
              178
            ]
          },
          {
            "kind": "expansion",
            "center": [
              5472,
              5904
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              169,
              183
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3072,
              1328
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              94,
              40
            ]
          },
          {
            "kind": "expansion",
            "center": [
              5792,
              1840
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              179,
              56
            ]
          }
        ],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 113,
          "center": [
            1952,
            752
          ],
          "depot_type": 106,
          "owner": 6,
          "top_left_tile": [
            59,
            22
          ]
        },
        "mineral_indices": [
          152,
          162,
          150,
          143,
          163
        ],
        "gas_indices": [
          144
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 1
        },
        "parent_site_index": 11,
        "group_index": 0,
        "group_sizes": [
          5
        ],
        "source_anchor": [
          1952,
          752
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              2816,
              4080
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              86,
              126
            ]
          },
          {
            "kind": "expansion",
            "center": [
              544,
              304
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              15,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              256,
              5744
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              6,
              178
            ]
          },
          {
            "kind": "expansion",
            "center": [
              5472,
              5904
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              169,
              183
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3072,
              1328
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              94,
              40
            ]
          },
          {
            "kind": "expansion",
            "center": [
              5792,
              1840
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              179,
              56
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            5792,
            1840
          ],
          "depot_type": 131,
          "owner": null,
          "top_left_tile": [
            179,
            56
          ]
        },
        "mineral_indices": [
          223,
          218,
          228,
          206,
          210
        ],
        "gas_indices": [
          234
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 1
        },
        "parent_site_index": 12,
        "group_index": 0,
        "group_sizes": [
          5
        ],
        "source_anchor": [
          5792,
          1840
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              2816,
              4080
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              86,
              126
            ]
          },
          {
            "kind": "expansion",
            "center": [
              544,
              304
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              15,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              256,
              5744
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              6,
              178
            ]
          },
          {
            "kind": "expansion",
            "center": [
              5472,
              5904
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              169,
              183
            ]
          },
          {
            "kind": "expansion",
            "center": [
              3072,
              1328
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              94,
              40
            ]
          },
          {
            "kind": "expansion",
            "center": [
              5792,
              1840
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              179,
              56
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      }
    ]
  },
  "614": {
    "input_unit_sha256": "170255866b4d6cf7c18ab4dad7248d2e8aedecbdb6a91591c46b2c3452fa473f",
    "moves": [
      {
        "index": 9,
        "before": [
          576,
          560,
          178,
          11
        ],
        "after": [
          416,
          112,
          178,
          11
        ]
      },
      {
        "index": 10,
        "before": [
          704,
          176,
          176,
          11
        ],
        "after": [
          736,
          144,
          176,
          11
        ]
      },
      {
        "index": 13,
        "before": [
          640,
          144,
          177,
          11
        ],
        "after": [
          672,
          144,
          177,
          11
        ]
      },
      {
        "index": 20,
        "before": [
          576,
          144,
          176,
          11
        ],
        "after": [
          288,
          176,
          176,
          11
        ]
      },
      {
        "index": 21,
        "before": [
          704,
          208,
          177,
          11
        ],
        "after": [
          768,
          176,
          177,
          11
        ]
      },
      {
        "index": 24,
        "before": [
          768,
          656,
          178,
          11
        ],
        "after": [
          608,
          112,
          178,
          11
        ]
      },
      {
        "index": 29,
        "before": [
          832,
          656,
          177,
          11
        ],
        "after": [
          768,
          240,
          177,
          11
        ]
      },
      {
        "index": 30,
        "before": [
          288,
          224,
          149,
          4
        ],
        "after": [
          736,
          352,
          149,
          4
        ]
      },
      {
        "index": 37,
        "before": [
          704,
          656,
          176,
          11
        ],
        "after": [
          544,
          112,
          176,
          11
        ]
      },
      {
        "index": 45,
        "before": [
          640,
          656,
          177,
          11
        ],
        "after": [
          480,
          112,
          177,
          11
        ]
      },
      {
        "index": 56,
        "before": [
          448,
          144,
          177,
          11
        ],
        "after": [
          224,
          240,
          177,
          11
        ]
      },
      {
        "index": 57,
        "before": [
          576,
          528,
          177,
          11
        ],
        "after": [
          352,
          144,
          177,
          11
        ]
      },
      {
        "index": 61,
        "before": [
          576,
          592,
          177,
          11
        ],
        "after": [
          320,
          272,
          177,
          11
        ]
      },
      {
        "index": 73,
        "before": [
          512,
          144,
          178,
          11
        ],
        "after": [
          256,
          208,
          178,
          11
        ]
      },
      {
        "index": 510,
        "before": [
          5888,
          1488,
          131,
          3
        ],
        "after": [
          5664,
          1328,
          131,
          3
        ]
      },
      {
        "index": 511,
        "before": [
          5696,
          1552,
          131,
          3
        ],
        "after": [
          5600,
          1552,
          131,
          3
        ]
      }
    ],
    "groups": [
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 486,
          "center": [
            512,
            304
          ],
          "depot_type": 133,
          "owner": 4,
          "top_left_tile": [
            14,
            8
          ]
        },
        "mineral_indices": [
          13,
          20,
          56,
          73,
          21,
          10,
          24,
          29,
          37,
          45,
          57,
          61,
          9
        ],
        "gas_indices": [
          30
        ],
        "status": "ladder_separate_gas",
        "reasons": {},
        "parent_site_index": 0,
        "group_index": 0,
        "group_sizes": [
          13
        ],
        "source_anchor": [
          512,
          304
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5216,
              304
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              161,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              4000,
              80
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              123,
              1
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "maximum_minerals": 13,
        "placement_policy": "reviewed_playtest_layout"
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 48,
          "center": [
            2400,
            240
          ],
          "depot_type": 106,
          "owner": 1,
          "top_left_tile": [
            73,
            6
          ]
        },
        "mineral_indices": [
          1,
          60,
          15,
          43,
          0,
          7,
          8,
          47,
          68,
          23,
          25,
          44
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 46,
          "plateau": 12
        },
        "parent_site_index": 1,
        "group_index": 0,
        "group_sizes": [
          12
        ],
        "source_anchor": [
          2400,
          240
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5216,
              304
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              161,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              4000,
              80
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              123,
              1
            ]
          }
        ],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            5216,
            304
          ],
          "depot_type": 131,
          "owner": null,
          "top_left_tile": [
            161,
            8
          ]
        },
        "mineral_indices": [
          145,
          78,
          91,
          132,
          97,
          115,
          79,
          92,
          146,
          69
        ],
        "gas_indices": [
          174
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 35,
          "geometry": 19
        },
        "parent_site_index": 2,
        "group_index": 0,
        "group_sizes": [
          10
        ],
        "source_anchor": [
          5216,
          304
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5216,
              304
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              161,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              4000,
              80
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              123,
              1
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 358,
          "center": [
            416,
            1616
          ],
          "depot_type": 106,
          "owner": 6,
          "top_left_tile": [
            11,
            49
          ]
        },
        "mineral_indices": [
          454,
          439,
          463,
          421,
          440,
          458,
          472,
          424,
          425,
          409
        ],
        "gas_indices": [
          445
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 168,
          "geometry": 62,
          "gas_exit": 2
        },
        "parent_site_index": 3,
        "group_index": 0,
        "group_sizes": [
          10
        ],
        "source_anchor": [
          416,
          1616
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5216,
              304
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              161,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              4000,
              80
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              123,
              1
            ]
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 515,
          "center": [
            5888,
            1648
          ],
          "depot_type": 131,
          "owner": 3,
          "top_left_tile": [
            182,
            50
          ]
        },
        "mineral_indices": [
          461,
          451,
          477,
          459,
          467,
          448,
          436,
          469,
          468
        ],
        "gas_indices": [
          478
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 22,
          "geometry": 24
        },
        "parent_site_index": 4,
        "group_index": 0,
        "group_sizes": [
          9
        ],
        "source_anchor": [
          5888,
          1648
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5216,
              304
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              161,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              4000,
              80
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              123,
              1
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 400,
          "center": [
            3456,
            1744
          ],
          "depot_type": 106,
          "owner": 1,
          "top_left_tile": [
            106,
            53
          ]
        },
        "mineral_indices": [
          247,
          261,
          269,
          270,
          334,
          252,
          253,
          341,
          260,
          342,
          259
        ],
        "gas_indices": [
          337
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 56
        },
        "parent_site_index": 5,
        "group_index": 0,
        "group_sizes": [
          11
        ],
        "source_anchor": [
          3456,
          1744
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5216,
              304
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              161,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              4000,
              80
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              123,
              1
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            4000,
            80
          ],
          "depot_type": 131,
          "owner": null,
          "top_left_tile": [
            123,
            1
          ]
        },
        "mineral_indices": [
          70,
          80,
          81,
          82,
          71
        ],
        "gas_indices": [
          99
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 104
        },
        "parent_site_index": 6,
        "group_index": 0,
        "group_sizes": [
          5
        ],
        "source_anchor": [
          4000,
          80
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5216,
              304
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              161,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              4000,
              80
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              123,
              1
            ]
          }
        ],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      }
    ]
  },
  "615": {
    "input_unit_sha256": "9f7e59d3d7bc1f603e682ddecebacf2177f030e74146e241459319695aa10538",
    "moves": [
      {
        "index": 9,
        "before": [
          576,
          560,
          178,
          11
        ],
        "after": [
          416,
          112,
          178,
          11
        ]
      },
      {
        "index": 10,
        "before": [
          704,
          176,
          176,
          11
        ],
        "after": [
          736,
          144,
          176,
          11
        ]
      },
      {
        "index": 13,
        "before": [
          640,
          144,
          177,
          11
        ],
        "after": [
          672,
          144,
          177,
          11
        ]
      },
      {
        "index": 20,
        "before": [
          576,
          144,
          176,
          11
        ],
        "after": [
          288,
          176,
          176,
          11
        ]
      },
      {
        "index": 21,
        "before": [
          704,
          208,
          177,
          11
        ],
        "after": [
          768,
          176,
          177,
          11
        ]
      },
      {
        "index": 24,
        "before": [
          768,
          656,
          178,
          11
        ],
        "after": [
          608,
          112,
          178,
          11
        ]
      },
      {
        "index": 29,
        "before": [
          832,
          656,
          177,
          11
        ],
        "after": [
          768,
          240,
          177,
          11
        ]
      },
      {
        "index": 30,
        "before": [
          288,
          224,
          149,
          4
        ],
        "after": [
          736,
          352,
          149,
          4
        ]
      },
      {
        "index": 37,
        "before": [
          704,
          656,
          176,
          11
        ],
        "after": [
          544,
          112,
          176,
          11
        ]
      },
      {
        "index": 45,
        "before": [
          640,
          656,
          177,
          11
        ],
        "after": [
          480,
          112,
          177,
          11
        ]
      },
      {
        "index": 56,
        "before": [
          448,
          144,
          177,
          11
        ],
        "after": [
          224,
          240,
          177,
          11
        ]
      },
      {
        "index": 57,
        "before": [
          576,
          528,
          177,
          11
        ],
        "after": [
          352,
          144,
          177,
          11
        ]
      },
      {
        "index": 61,
        "before": [
          576,
          592,
          177,
          11
        ],
        "after": [
          320,
          272,
          177,
          11
        ]
      },
      {
        "index": 73,
        "before": [
          512,
          144,
          178,
          11
        ],
        "after": [
          256,
          208,
          178,
          11
        ]
      },
      {
        "index": 512,
        "before": [
          5888,
          1488,
          131,
          3
        ],
        "after": [
          5664,
          1328,
          131,
          3
        ]
      },
      {
        "index": 513,
        "before": [
          5696,
          1552,
          131,
          3
        ],
        "after": [
          5600,
          1552,
          131,
          3
        ]
      }
    ],
    "groups": [
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 488,
          "center": [
            512,
            304
          ],
          "depot_type": 133,
          "owner": 4,
          "top_left_tile": [
            14,
            8
          ]
        },
        "mineral_indices": [
          13,
          20,
          56,
          73,
          21,
          10,
          24,
          29,
          37,
          45,
          57,
          61,
          9
        ],
        "gas_indices": [
          30
        ],
        "status": "ladder_separate_gas",
        "reasons": {},
        "parent_site_index": 0,
        "group_index": 0,
        "group_sizes": [
          13
        ],
        "source_anchor": [
          512,
          304
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5216,
              304
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              161,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              4000,
              80
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              123,
              1
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "maximum_minerals": 13,
        "placement_policy": "reviewed_playtest_layout"
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 48,
          "center": [
            2400,
            240
          ],
          "depot_type": 106,
          "owner": 1,
          "top_left_tile": [
            73,
            6
          ]
        },
        "mineral_indices": [
          1,
          60,
          15,
          43,
          0,
          7,
          8,
          47,
          68,
          23,
          25,
          44
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 46,
          "plateau": 12
        },
        "parent_site_index": 1,
        "group_index": 0,
        "group_sizes": [
          12
        ],
        "source_anchor": [
          2400,
          240
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5216,
              304
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              161,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              4000,
              80
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              123,
              1
            ]
          }
        ],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            5216,
            304
          ],
          "depot_type": 131,
          "owner": null,
          "top_left_tile": [
            161,
            8
          ]
        },
        "mineral_indices": [
          145,
          78,
          91,
          132,
          97,
          115,
          79,
          92,
          146,
          69
        ],
        "gas_indices": [
          174
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 35,
          "geometry": 19
        },
        "parent_site_index": 2,
        "group_index": 0,
        "group_sizes": [
          10
        ],
        "source_anchor": [
          5216,
          304
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5216,
              304
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              161,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              4000,
              80
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              123,
              1
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 358,
          "center": [
            416,
            1616
          ],
          "depot_type": 106,
          "owner": 6,
          "top_left_tile": [
            11,
            49
          ]
        },
        "mineral_indices": [
          456,
          441,
          465,
          422,
          442,
          460,
          474,
          425,
          426,
          410
        ],
        "gas_indices": [
          447
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 168,
          "geometry": 62,
          "gas_exit": 2
        },
        "parent_site_index": 3,
        "group_index": 0,
        "group_sizes": [
          10
        ],
        "source_anchor": [
          416,
          1616
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5216,
              304
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              161,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              4000,
              80
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              123,
              1
            ]
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 517,
          "center": [
            5888,
            1648
          ],
          "depot_type": 131,
          "owner": 3,
          "top_left_tile": [
            182,
            50
          ]
        },
        "mineral_indices": [
          463,
          453,
          479,
          461,
          469,
          450,
          437,
          471,
          470
        ],
        "gas_indices": [
          480
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 22,
          "geometry": 24
        },
        "parent_site_index": 4,
        "group_index": 0,
        "group_sizes": [
          9
        ],
        "source_anchor": [
          5888,
          1648
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5216,
              304
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              161,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              4000,
              80
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              123,
              1
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 400,
          "center": [
            3456,
            1744
          ],
          "depot_type": 106,
          "owner": 1,
          "top_left_tile": [
            106,
            53
          ]
        },
        "mineral_indices": [
          247,
          261,
          269,
          270,
          334,
          252,
          253,
          341,
          260,
          342,
          259
        ],
        "gas_indices": [
          337
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 56
        },
        "parent_site_index": 5,
        "group_index": 0,
        "group_sizes": [
          11
        ],
        "source_anchor": [
          3456,
          1744
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5216,
              304
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              161,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              4000,
              80
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              123,
              1
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            4000,
            80
          ],
          "depot_type": 131,
          "owner": null,
          "top_left_tile": [
            123,
            1
          ]
        },
        "mineral_indices": [
          70,
          80,
          81,
          82,
          71
        ],
        "gas_indices": [
          99
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 104
        },
        "parent_site_index": 6,
        "group_index": 0,
        "group_sizes": [
          5
        ],
        "source_anchor": [
          4000,
          80
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5216,
              304
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              161,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              4000,
              80
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              123,
              1
            ]
          }
        ],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      }
    ]
  },
  "616": {
    "input_unit_sha256": "967433a621a25a7bde3fafc87cc31091a9aa378b9c264680e3dee97059296bea",
    "moves": [
      {
        "index": 9,
        "before": [
          576,
          560,
          178,
          11
        ],
        "after": [
          416,
          112,
          178,
          11
        ]
      },
      {
        "index": 10,
        "before": [
          704,
          176,
          176,
          11
        ],
        "after": [
          736,
          144,
          176,
          11
        ]
      },
      {
        "index": 13,
        "before": [
          640,
          144,
          177,
          11
        ],
        "after": [
          672,
          144,
          177,
          11
        ]
      },
      {
        "index": 20,
        "before": [
          576,
          144,
          176,
          11
        ],
        "after": [
          288,
          176,
          176,
          11
        ]
      },
      {
        "index": 21,
        "before": [
          704,
          208,
          177,
          11
        ],
        "after": [
          768,
          176,
          177,
          11
        ]
      },
      {
        "index": 24,
        "before": [
          768,
          656,
          178,
          11
        ],
        "after": [
          608,
          112,
          178,
          11
        ]
      },
      {
        "index": 29,
        "before": [
          832,
          656,
          177,
          11
        ],
        "after": [
          768,
          240,
          177,
          11
        ]
      },
      {
        "index": 30,
        "before": [
          288,
          224,
          149,
          4
        ],
        "after": [
          736,
          352,
          149,
          4
        ]
      },
      {
        "index": 37,
        "before": [
          704,
          656,
          176,
          11
        ],
        "after": [
          544,
          112,
          176,
          11
        ]
      },
      {
        "index": 45,
        "before": [
          640,
          656,
          177,
          11
        ],
        "after": [
          480,
          112,
          177,
          11
        ]
      },
      {
        "index": 56,
        "before": [
          448,
          144,
          177,
          11
        ],
        "after": [
          224,
          240,
          177,
          11
        ]
      },
      {
        "index": 57,
        "before": [
          576,
          528,
          177,
          11
        ],
        "after": [
          352,
          144,
          177,
          11
        ]
      },
      {
        "index": 61,
        "before": [
          576,
          592,
          177,
          11
        ],
        "after": [
          320,
          272,
          177,
          11
        ]
      },
      {
        "index": 73,
        "before": [
          512,
          144,
          178,
          11
        ],
        "after": [
          256,
          208,
          178,
          11
        ]
      },
      {
        "index": 514,
        "before": [
          5888,
          1488,
          131,
          3
        ],
        "after": [
          5664,
          1328,
          131,
          3
        ]
      },
      {
        "index": 515,
        "before": [
          5696,
          1552,
          131,
          3
        ],
        "after": [
          5600,
          1552,
          131,
          3
        ]
      }
    ],
    "groups": [
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 490,
          "center": [
            512,
            304
          ],
          "depot_type": 133,
          "owner": 4,
          "top_left_tile": [
            14,
            8
          ]
        },
        "mineral_indices": [
          13,
          20,
          56,
          73,
          21,
          10,
          24,
          29,
          37,
          45,
          57,
          61,
          9
        ],
        "gas_indices": [
          30
        ],
        "status": "ladder_separate_gas",
        "reasons": {},
        "parent_site_index": 0,
        "group_index": 0,
        "group_sizes": [
          13
        ],
        "source_anchor": [
          512,
          304
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5216,
              304
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              161,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              4000,
              80
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              123,
              1
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "maximum_minerals": 13,
        "placement_policy": "reviewed_playtest_layout"
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 48,
          "center": [
            2400,
            240
          ],
          "depot_type": 106,
          "owner": 1,
          "top_left_tile": [
            73,
            6
          ]
        },
        "mineral_indices": [
          1,
          60,
          15,
          43,
          0,
          7,
          8,
          47,
          68,
          23,
          25,
          44
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 46,
          "plateau": 12
        },
        "parent_site_index": 1,
        "group_index": 0,
        "group_sizes": [
          12
        ],
        "source_anchor": [
          2400,
          240
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5216,
              304
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              161,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              4000,
              80
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              123,
              1
            ]
          }
        ],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            5216,
            304
          ],
          "depot_type": 131,
          "owner": null,
          "top_left_tile": [
            161,
            8
          ]
        },
        "mineral_indices": [
          145,
          78,
          91,
          132,
          97,
          115,
          79,
          92,
          146,
          69
        ],
        "gas_indices": [
          174
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 35,
          "geometry": 19
        },
        "parent_site_index": 2,
        "group_index": 0,
        "group_sizes": [
          10
        ],
        "source_anchor": [
          5216,
          304
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5216,
              304
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              161,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              4000,
              80
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              123,
              1
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 359,
          "center": [
            416,
            1616
          ],
          "depot_type": 106,
          "owner": 6,
          "top_left_tile": [
            11,
            49
          ]
        },
        "mineral_indices": [
          458,
          443,
          467,
          424,
          444,
          462,
          476,
          427,
          428,
          412
        ],
        "gas_indices": [
          449
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 168,
          "geometry": 62,
          "gas_exit": 2
        },
        "parent_site_index": 3,
        "group_index": 0,
        "group_sizes": [
          10
        ],
        "source_anchor": [
          416,
          1616
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5216,
              304
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              161,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              4000,
              80
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              123,
              1
            ]
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 519,
          "center": [
            5888,
            1648
          ],
          "depot_type": 131,
          "owner": 3,
          "top_left_tile": [
            182,
            50
          ]
        },
        "mineral_indices": [
          465,
          455,
          481,
          463,
          471,
          452,
          439,
          473,
          472
        ],
        "gas_indices": [
          482
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 22,
          "geometry": 24
        },
        "parent_site_index": 4,
        "group_index": 0,
        "group_sizes": [
          9
        ],
        "source_anchor": [
          5888,
          1648
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5216,
              304
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              161,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              4000,
              80
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              123,
              1
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 402,
          "center": [
            3456,
            1744
          ],
          "depot_type": 106,
          "owner": 1,
          "top_left_tile": [
            106,
            53
          ]
        },
        "mineral_indices": [
          247,
          261,
          269,
          270,
          334,
          252,
          253,
          341,
          260,
          342,
          259
        ],
        "gas_indices": [
          337
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 56
        },
        "parent_site_index": 5,
        "group_index": 0,
        "group_sizes": [
          11
        ],
        "source_anchor": [
          3456,
          1744
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5216,
              304
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              161,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              4000,
              80
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              123,
              1
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            4000,
            80
          ],
          "depot_type": 131,
          "owner": null,
          "top_left_tile": [
            123,
            1
          ]
        },
        "mineral_indices": [
          70,
          80,
          81,
          82,
          71
        ],
        "gas_indices": [
          99
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 104
        },
        "parent_site_index": 6,
        "group_index": 0,
        "group_sizes": [
          5
        ],
        "source_anchor": [
          4000,
          80
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5216,
              304
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              161,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              4000,
              80
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              123,
              1
            ]
          }
        ],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      }
    ]
  },
  "617": {
    "input_unit_sha256": "ceea1e28a88ee4aa1ac54bea03e129198a7573cf07f2e8172122420701e0bd25",
    "moves": [
      {
        "index": 9,
        "before": [
          576,
          560,
          178,
          11
        ],
        "after": [
          416,
          112,
          178,
          11
        ]
      },
      {
        "index": 10,
        "before": [
          704,
          176,
          176,
          11
        ],
        "after": [
          736,
          144,
          176,
          11
        ]
      },
      {
        "index": 13,
        "before": [
          640,
          144,
          177,
          11
        ],
        "after": [
          672,
          144,
          177,
          11
        ]
      },
      {
        "index": 20,
        "before": [
          576,
          144,
          176,
          11
        ],
        "after": [
          288,
          176,
          176,
          11
        ]
      },
      {
        "index": 21,
        "before": [
          704,
          208,
          177,
          11
        ],
        "after": [
          768,
          176,
          177,
          11
        ]
      },
      {
        "index": 24,
        "before": [
          768,
          656,
          178,
          11
        ],
        "after": [
          608,
          112,
          178,
          11
        ]
      },
      {
        "index": 29,
        "before": [
          832,
          656,
          177,
          11
        ],
        "after": [
          768,
          240,
          177,
          11
        ]
      },
      {
        "index": 30,
        "before": [
          288,
          224,
          149,
          4
        ],
        "after": [
          736,
          352,
          149,
          4
        ]
      },
      {
        "index": 37,
        "before": [
          704,
          656,
          176,
          11
        ],
        "after": [
          544,
          112,
          176,
          11
        ]
      },
      {
        "index": 45,
        "before": [
          640,
          656,
          177,
          11
        ],
        "after": [
          480,
          112,
          177,
          11
        ]
      },
      {
        "index": 56,
        "before": [
          448,
          144,
          177,
          11
        ],
        "after": [
          224,
          240,
          177,
          11
        ]
      },
      {
        "index": 57,
        "before": [
          576,
          528,
          177,
          11
        ],
        "after": [
          352,
          144,
          177,
          11
        ]
      },
      {
        "index": 61,
        "before": [
          576,
          592,
          177,
          11
        ],
        "after": [
          320,
          272,
          177,
          11
        ]
      },
      {
        "index": 73,
        "before": [
          512,
          144,
          178,
          11
        ],
        "after": [
          256,
          208,
          178,
          11
        ]
      },
      {
        "index": 516,
        "before": [
          5888,
          1488,
          131,
          3
        ],
        "after": [
          5664,
          1328,
          131,
          3
        ]
      },
      {
        "index": 517,
        "before": [
          5696,
          1552,
          131,
          3
        ],
        "after": [
          5600,
          1552,
          131,
          3
        ]
      }
    ],
    "groups": [
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 492,
          "center": [
            512,
            304
          ],
          "depot_type": 133,
          "owner": 4,
          "top_left_tile": [
            14,
            8
          ]
        },
        "mineral_indices": [
          13,
          20,
          56,
          73,
          21,
          10,
          24,
          29,
          37,
          45,
          57,
          61,
          9
        ],
        "gas_indices": [
          30
        ],
        "status": "ladder_separate_gas",
        "reasons": {},
        "parent_site_index": 0,
        "group_index": 0,
        "group_sizes": [
          13
        ],
        "source_anchor": [
          512,
          304
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5216,
              304
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              161,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              4000,
              80
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              123,
              1
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "maximum_minerals": 13,
        "placement_policy": "reviewed_playtest_layout"
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 48,
          "center": [
            2400,
            240
          ],
          "depot_type": 106,
          "owner": 1,
          "top_left_tile": [
            73,
            6
          ]
        },
        "mineral_indices": [
          1,
          60,
          15,
          43,
          0,
          7,
          8,
          47,
          68,
          23,
          25,
          44
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 46,
          "plateau": 12
        },
        "parent_site_index": 1,
        "group_index": 0,
        "group_sizes": [
          12
        ],
        "source_anchor": [
          2400,
          240
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5216,
              304
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              161,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              4000,
              80
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              123,
              1
            ]
          }
        ],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            5216,
            304
          ],
          "depot_type": 131,
          "owner": null,
          "top_left_tile": [
            161,
            8
          ]
        },
        "mineral_indices": [
          145,
          78,
          91,
          132,
          97,
          115,
          79,
          92,
          146,
          69
        ],
        "gas_indices": [
          174
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 35,
          "geometry": 19
        },
        "parent_site_index": 2,
        "group_index": 0,
        "group_sizes": [
          10
        ],
        "source_anchor": [
          5216,
          304
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5216,
              304
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              161,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              4000,
              80
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              123,
              1
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 359,
          "center": [
            416,
            1616
          ],
          "depot_type": 106,
          "owner": 6,
          "top_left_tile": [
            11,
            49
          ]
        },
        "mineral_indices": [
          458,
          443,
          468,
          424,
          444,
          462,
          477,
          427,
          428,
          412
        ],
        "gas_indices": [
          449
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 168,
          "geometry": 62,
          "gas_exit": 2
        },
        "parent_site_index": 3,
        "group_index": 0,
        "group_sizes": [
          10
        ],
        "source_anchor": [
          416,
          1616
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5216,
              304
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              161,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              4000,
              80
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              123,
              1
            ]
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 521,
          "center": [
            5888,
            1648
          ],
          "depot_type": 131,
          "owner": 3,
          "top_left_tile": [
            182,
            50
          ]
        },
        "mineral_indices": [
          466,
          455,
          482,
          463,
          472,
          452,
          439,
          474,
          473
        ],
        "gas_indices": [
          483
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 22,
          "geometry": 24
        },
        "parent_site_index": 4,
        "group_index": 0,
        "group_sizes": [
          9
        ],
        "source_anchor": [
          5888,
          1648
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5216,
              304
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              161,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              4000,
              80
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              123,
              1
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 402,
          "center": [
            3456,
            1744
          ],
          "depot_type": 106,
          "owner": 1,
          "top_left_tile": [
            106,
            53
          ]
        },
        "mineral_indices": [
          247,
          261,
          269,
          270,
          334,
          252,
          253,
          341,
          260,
          342,
          259
        ],
        "gas_indices": [
          337
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 56
        },
        "parent_site_index": 5,
        "group_index": 0,
        "group_sizes": [
          11
        ],
        "source_anchor": [
          3456,
          1744
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5216,
              304
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              161,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              4000,
              80
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              123,
              1
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            4000,
            80
          ],
          "depot_type": 131,
          "owner": null,
          "top_left_tile": [
            123,
            1
          ]
        },
        "mineral_indices": [
          70,
          80,
          81,
          82,
          71
        ],
        "gas_indices": [
          99
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 104
        },
        "parent_site_index": 6,
        "group_index": 0,
        "group_sizes": [
          5
        ],
        "source_anchor": [
          4000,
          80
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5216,
              304
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              161,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              4000,
              80
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              123,
              1
            ]
          }
        ],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      }
    ]
  },
  "618": {
    "input_unit_sha256": "671d53fe00ef5130f3bec36f8b75b55fa82ad2f154a9c299e40d3b22b1321b32",
    "moves": [
      {
        "index": 9,
        "before": [
          576,
          560,
          178,
          11
        ],
        "after": [
          416,
          112,
          178,
          11
        ]
      },
      {
        "index": 10,
        "before": [
          704,
          176,
          176,
          11
        ],
        "after": [
          736,
          144,
          176,
          11
        ]
      },
      {
        "index": 13,
        "before": [
          640,
          144,
          177,
          11
        ],
        "after": [
          672,
          144,
          177,
          11
        ]
      },
      {
        "index": 20,
        "before": [
          576,
          144,
          176,
          11
        ],
        "after": [
          288,
          176,
          176,
          11
        ]
      },
      {
        "index": 21,
        "before": [
          704,
          208,
          177,
          11
        ],
        "after": [
          768,
          176,
          177,
          11
        ]
      },
      {
        "index": 24,
        "before": [
          768,
          656,
          178,
          11
        ],
        "after": [
          608,
          112,
          178,
          11
        ]
      },
      {
        "index": 29,
        "before": [
          832,
          656,
          177,
          11
        ],
        "after": [
          768,
          240,
          177,
          11
        ]
      },
      {
        "index": 30,
        "before": [
          288,
          224,
          149,
          4
        ],
        "after": [
          736,
          352,
          149,
          4
        ]
      },
      {
        "index": 37,
        "before": [
          704,
          656,
          176,
          11
        ],
        "after": [
          544,
          112,
          176,
          11
        ]
      },
      {
        "index": 45,
        "before": [
          640,
          656,
          177,
          11
        ],
        "after": [
          480,
          112,
          177,
          11
        ]
      },
      {
        "index": 56,
        "before": [
          448,
          144,
          177,
          11
        ],
        "after": [
          224,
          240,
          177,
          11
        ]
      },
      {
        "index": 57,
        "before": [
          576,
          528,
          177,
          11
        ],
        "after": [
          352,
          144,
          177,
          11
        ]
      },
      {
        "index": 61,
        "before": [
          576,
          592,
          177,
          11
        ],
        "after": [
          320,
          272,
          177,
          11
        ]
      },
      {
        "index": 73,
        "before": [
          512,
          144,
          178,
          11
        ],
        "after": [
          256,
          208,
          178,
          11
        ]
      },
      {
        "index": 518,
        "before": [
          5888,
          1488,
          131,
          3
        ],
        "after": [
          5664,
          1328,
          131,
          3
        ]
      },
      {
        "index": 519,
        "before": [
          5696,
          1552,
          131,
          3
        ],
        "after": [
          5600,
          1552,
          131,
          3
        ]
      }
    ],
    "groups": [
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 494,
          "center": [
            512,
            304
          ],
          "depot_type": 133,
          "owner": 4,
          "top_left_tile": [
            14,
            8
          ]
        },
        "mineral_indices": [
          13,
          20,
          56,
          73,
          21,
          10,
          24,
          29,
          37,
          45,
          57,
          61,
          9
        ],
        "gas_indices": [
          30
        ],
        "status": "ladder_separate_gas",
        "reasons": {},
        "parent_site_index": 0,
        "group_index": 0,
        "group_sizes": [
          13
        ],
        "source_anchor": [
          512,
          304
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5216,
              304
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              161,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              4000,
              80
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              123,
              1
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "maximum_minerals": 13,
        "placement_policy": "reviewed_playtest_layout"
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 48,
          "center": [
            2400,
            240
          ],
          "depot_type": 106,
          "owner": 1,
          "top_left_tile": [
            73,
            6
          ]
        },
        "mineral_indices": [
          1,
          60,
          15,
          43,
          0,
          7,
          8,
          47,
          68,
          23,
          25,
          44
        ],
        "gas_indices": [],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 46,
          "plateau": 12
        },
        "parent_site_index": 1,
        "group_index": 0,
        "group_sizes": [
          12
        ],
        "source_anchor": [
          2400,
          240
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5216,
              304
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              161,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              4000,
              80
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              123,
              1
            ]
          }
        ],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            5216,
            304
          ],
          "depot_type": 131,
          "owner": null,
          "top_left_tile": [
            161,
            8
          ]
        },
        "mineral_indices": [
          145,
          78,
          91,
          132,
          97,
          115,
          79,
          92,
          146,
          69
        ],
        "gas_indices": [
          174
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 35,
          "geometry": 19
        },
        "parent_site_index": 2,
        "group_index": 0,
        "group_sizes": [
          10
        ],
        "source_anchor": [
          5216,
          304
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5216,
              304
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              161,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              4000,
              80
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              123,
              1
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 359,
          "center": [
            416,
            1616
          ],
          "depot_type": 106,
          "owner": 6,
          "top_left_tile": [
            11,
            49
          ]
        },
        "mineral_indices": [
          460,
          445,
          470,
          425,
          446,
          464,
          479,
          428,
          429,
          413
        ],
        "gas_indices": [
          451
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 168,
          "geometry": 62,
          "gas_exit": 2
        },
        "parent_site_index": 3,
        "group_index": 0,
        "group_sizes": [
          10
        ],
        "source_anchor": [
          416,
          1616
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5216,
              304
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              161,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              4000,
              80
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              123,
              1
            ]
          }
        ],
        "direction": [
          1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 523,
          "center": [
            5888,
            1648
          ],
          "depot_type": 131,
          "owner": 3,
          "top_left_tile": [
            182,
            50
          ]
        },
        "mineral_indices": [
          468,
          457,
          484,
          465,
          474,
          454,
          440,
          476,
          475
        ],
        "gas_indices": [
          485
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 22,
          "geometry": 24
        },
        "parent_site_index": 4,
        "group_index": 0,
        "group_sizes": [
          9
        ],
        "source_anchor": [
          5888,
          1648
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5216,
              304
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              161,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              4000,
              80
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              123,
              1
            ]
          }
        ],
        "direction": [
          0,
          -1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "existing_depot",
          "unit_index": 402,
          "center": [
            3456,
            1744
          ],
          "depot_type": 106,
          "owner": 1,
          "top_left_tile": [
            106,
            53
          ]
        },
        "mineral_indices": [
          247,
          261,
          269,
          270,
          334,
          252,
          253,
          341,
          260,
          342,
          259
        ],
        "gas_indices": [
          337
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "geometry": 56
        },
        "parent_site_index": 5,
        "group_index": 0,
        "group_sizes": [
          11
        ],
        "source_anchor": [
          3456,
          1744
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5216,
              304
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              161,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              4000,
              80
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              123,
              1
            ]
          }
        ],
        "direction": [
          0,
          1
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      },
      {
        "anchor": {
          "kind": "expansion",
          "center": [
            4000,
            80
          ],
          "depot_type": 131,
          "owner": null,
          "top_left_tile": [
            123,
            1
          ]
        },
        "mineral_indices": [
          70,
          80,
          81,
          82,
          71
        ],
        "gas_indices": [
          99
        ],
        "status": "ladder_separate_gas",
        "reasons": {
          "plateau": 104
        },
        "parent_site_index": 6,
        "group_index": 0,
        "group_sizes": [
          5
        ],
        "source_anchor": [
          4000,
          80
        ],
        "planned_depot_sites": [
          {
            "kind": "expansion",
            "center": [
              5216,
              304
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              161,
              8
            ]
          },
          {
            "kind": "expansion",
            "center": [
              4000,
              80
            ],
            "depot_type": 131,
            "owner": null,
            "top_left_tile": [
              123,
              1
            ]
          }
        ],
        "direction": [
          -1,
          0
        ],
        "formation": "reviewed_single_layer",
        "rows": 1,
        "placement_policy": "reviewed_playtest_layout",
        "maximum_minerals": 12
      }
    ]
  }
}
''')
