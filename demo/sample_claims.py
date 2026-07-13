"""
Five realistic German insurance claim submissions for the demo.

Scenarios cover different perils, severity levels, and completeness —
mirroring the variance a real insurer sees in daily claim intake.
"""

SAMPLE_CLAIMS: list[tuple[str, str, dict]] = [
    # (claim_id, claim_text, expected_highlights)
    (
        "CLM-2024-MUC-001",
        """
        Policyholder: Anna Müller
        Policy number: HAV-MUC-88432
        Date of incident: 10 June 2024

        Dear Claims Team,

        I am writing to report a water damage incident at my apartment located at
        Schillerstraße 14, 80336 Munich. On the evening of 10 June, a pipe behind
        the bathroom wall burst without warning. By the time we discovered the leak
        the water had spread throughout the hallway and into the living room.

        The parquet flooring in the hallway (approx. 18 m²) has warped beyond repair
        and the drywall along one living room wall is soaked and will need full
        replacement. A plumber arrived the next morning and confirmed the pipe had
        corroded through — he provided a preliminary report.

        I estimate the total repair cost at around €8,500 based on quotes I am still
        gathering. Please let me know which documents you require.

        Kind regards,
        Anna Müller
        """,
        {"expected_peril": "water_damage", "expected_severity": "medium"},
    ),
    (
        "CLM-2024-BER-002",
        """
        Claimant: Thomas Berger
        Address: Prenzlauer Allee 77, 10405 Berlin
        Policy: HHV-BER-29107

        Incident: Residential burglary
        Date: 14 July 2024, overnight (estimated between 23:00 and 06:00)

        Our apartment was broken into while we were away for the weekend.
        The perpetrators forced the balcony door (2nd floor). Items stolen include:
        MacBook Pro (approx. €2,200), camera equipment (Canon EOS R5, two lenses, ~€5,000),
        jewellery (estimated €3,000), and €400 cash.

        A police report has been filed at Polizeidienststelle Prenzlauer Berg,
        reference number: PD-BER-2024-078234. A copy is attached.

        Total claimed: approximately €10,600.

        Thomas Berger
        """,
        {"expected_peril": "theft_burglary", "expected_severity": "high"},
    ),
    (
        "CLM-2024-STU-003",
        """
        Good afternoon,

        I'd like to claim for hail damage to my car. There was a severe hailstorm
        here in Stuttgart last Thursday. My car, a 2021 VW Golf (licence plate
        S-KB-4421), was parked outside on Königstraße and has multiple dents across
        the bonnet, roof and boot lid. The windscreen also has a crack.

        I have photos. Don't know the repair cost yet — haven't been to a garage.

        Best,
        Klaus Brandt
        """,
        {"expected_peril": "vehicle", "expected_severity": "medium"},
    ),
    (
        "CLM-2024-HAM-004",
        """
        URGENT — Fire damage to kitchen

        Name: Fatima Al-Hassan
        Address: Elbchaussee 200, 22605 Hamburg
        Policy number: GHV-HAM-51903

        On 2 August 2024 at approximately 13:15, a fire started in the kitchen of
        our house. The cause appears to be an electrical fault in the built-in oven.
        The fire spread to the kitchen cupboards and part of the ceiling before the
        fire brigade arrived and extinguished it.

        The kitchen is a complete write-off. Smoke damage has also affected the
        adjacent dining room and hallway. Structural assessment has not yet been
        carried out — the fire brigade has flagged a possible load-bearing wall
        concern and advised us not to use the kitchen or dining room.

        Fire brigade report reference: FW-HH-2024-0802-0047.

        We are currently staying with relatives. Total loss estimate is unknown
        pending structural survey. Please escalate as a priority claim.

        Fatima Al-Hassan
        +49 151 3344 5566
        """,
        {"expected_peril": "fire", "expected_severity": "extreme"},
    ),
    (
        "CLM-2024-FFM-005",
        """
        Wind / storm damage — roof tiles and garden shed
        Date of loss: 19 October 2024

        The storm last Friday (Sturmtief "Axel") caused significant damage to our
        property in Frankfurt. Approximately 30 roof tiles were displaced or broken
        on the west-facing slope of our detached house; two of them fell into the
        garden but fortunately nobody was injured. We put a tarpaulin over the
        exposed section but rain has already penetrated into the attic space.

        The garden shed (approx. 4 × 3 m) was completely destroyed — the roof
        came off and the walls collapsed. Contents inside (lawnmower, tools) are
        damaged.

        I don't yet have a repair estimate for the roof. I'd like to claim for:
        — Roof repair (tiling + underlay): estimated €4,000–5,500
        — Shed replacement: ~€1,800
        — Lawnmower and tools: ~€600

        Policy: GHV-FFM-30041
        Name: Peter Hoffmann
        Location: Am Sachsenhäuser Berg 12, 60594 Frankfurt am Main
        """,
        {"expected_peril": "natural_hazard", "expected_severity": "high"},
    ),
]
