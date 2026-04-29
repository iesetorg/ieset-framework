# Positions Map — Taxonomy Review

Draft taxonomy for the musicmap.info-style visualisation of the 17 positions. This doc exists to be sanity-checked before any rendering code is written — every number and relationship below should be either accepted, adjusted, or pushed back on.

## The 7 families (super-clusters)

Musicmap has 23 super-genres colour-coded as three primary currents (Rock, EDM, Blue Note). For the political-economy map, 7 families keep the picture legible without collapsing distinctions that matter empirically.

| Family | Positions | Core commitment |
|---|---|---|
| `market_liberal` | classical_liberal, austrian, chicago_monetarism | Voluntary exchange + property rights as default; state scope narrow |
| `institutional_mainstream` | ordoliberal, new_keynesian, empirical_pragmatist, institutionalism | Markets default, but with strong institutional scaffolding and conditional activism |
| `developmentalist` | developmentalism | Late-developer state-led catch-up with selective market engagement |
| `post_keynesian_heterodox` | post_keynesian, mmt | Demand-first, endogenous money, markets preserved but insufficient |
| `democratic_socialist_reformist` | social_democratic, democratic_socialist, market_socialist | Expanded public ownership and universal services via democratic means |
| `marxist_revolutionary` | marxian, marxist_leninist | Structural anti-capitalism; distribution not corrigible within capitalism |
| `ecological` | degrowth, eco_socialist | Growth-constrained; planetary limits override production priorities |

### Why 7 and not 5 or 10

- **Why not fewer**: lumping `developmentalism` into either `institutional_mainstream` or `post_keynesian_heterodox` loses Chang's "kicking away the ladder" argument, which is genuinely anti-Washington-Consensus without being heterodox on demand. Likewise, collapsing `ecological` into `marxist` erases the degrowth wing that is institutionally plural.
- **Why not more**: `market_socialist` could sit in its own bucket between Keynesian heterodoxy and revolutionary Marxism, but the empirical record (Mondragón, Meidner, Yugoslav self-management) puts it closer to the democratic-socialist reformist branch than to either revolutionary Marxism or post-Keynesian demand theory.

## Positions — full taxonomy table

Vertical axis on the map = `origin_year`. Horizontal = `spectrum_x` (-1 collectivist / +1 market-liberal). Arrows = `parent_position_ids` (primary influence) and `anti_link_ids` (explicit backlash).

| Position | Family | Origin | Spectrum x | Parents | Anti-links |
|---|---|---:|---:|---|---|
| classical_liberal | market_liberal | 1776 | +0.80 | — | — |
| marxian | marxist_revolutionary | 1867 | −0.90 | — | classical_liberal |
| democratic_socialist | democratic_socialist_reformist | 1899 | −0.70 | marxian | marxist_leninist |
| austrian | market_liberal | 1912 | +0.95 | classical_liberal | marxist_leninist |
| marxist_leninist | marxist_revolutionary | 1917 | −0.95 | marxian | social_democratic |
| ordoliberal | institutional_mainstream | 1932 | +0.50 | classical_liberal | marxist_leninist |
| market_socialist | democratic_socialist_reformist | 1937 | −0.50 | marxian | austrian |
| developmentalism | developmentalist | 1950 | −0.10 | post_keynesian | chicago_monetarism |
| post_keynesian | post_keynesian_heterodox | 1956 | −0.30 | — | chicago_monetarism, new_keynesian |
| social_democratic | democratic_socialist_reformist | 1959 | −0.40 | democratic_socialist | — |
| chicago_monetarism | market_liberal | 1963 | +0.85 | classical_liberal | post_keynesian |
| degrowth | ecological | 1977 | −0.70 | post_keynesian | new_keynesian |
| new_keynesian | institutional_mainstream | 1985 | +0.20 | post_keynesian, chicago_monetarism | austrian |
| institutionalism | institutional_mainstream | 1990 | +0.30 | classical_liberal | — |
| mmt | post_keynesian_heterodox | 1996 | −0.50 | post_keynesian | chicago_monetarism |
| eco_socialist | ecological | 2000 | −0.85 | marxian, degrowth | classical_liberal |
| empirical_pragmatist | institutional_mainstream | 2007 | +0.25 | institutionalism | — |

## Placement rationale — what to push back on

The pieces most worth scrutinising, each stated as the assumption the map is currently making.

### Origin years

Chosen as the landmark text or school-founding moment, not the peak influence.

- **classical_liberal = 1776** (*Wealth of Nations*) — uncontroversial.
- **austrian = 1912** (Mises, *Theory of Money and Credit*). Menger 1871 founded the Austrian School as a marginalist tradition, but ABCT specifically is a Mises-Hayek product; 1912 picks Mises's money book as the first ABCT-relevant landmark. Alternative: 1871 if we want "Austrian School" broadly rather than ABCT specifically.
- **marxian = 1867** (*Das Kapital* Vol. I) — uncontroversial.
- **marxist_leninist = 1917** (*State and Revolution*). Alternative: 1902 (*What Is to Be Done?*).
- **ordoliberal = 1932** (Freiburg School formation; Eucken's *Grundsätze* 1952 is later). Alternative: 1952.
- **market_socialist = 1937** (Lange, *On the Economic Theory of Socialism* complete).
- **developmentalism = 1950** (Prebisch thesis). Alternative: 1943 (Rosenstein-Rodan) if we want to pick up the earliest structuralist landmark.
- **post_keynesian = 1956** (Robinson, *Accumulation of Capital*). Alternative: 1986 (Minsky) if we want the financial-instability-dominated reading.
- **social_democratic = 1959** (SPD Bad Godesberg programmatic moderation). Alternative: 1899 if we treat social-democracy as co-founded with democratic-socialism via Bernstein — but then the two collapse. The 1959 date preserves the distinction between reformist-with-socialist-telos (1899) and reformist-accepting-mixed-economy (1959).
- **chicago_monetarism = 1963** (*A Monetary History*). Alternative: 1956 (Friedman's "Quantity Theory Restatement").
- **degrowth = 1977** (Daly, *Steady-State Economics*). Alternative: 2002 (Latouche coins "degrowth"). The 1977 date privileges the steady-state lineage over the French movement; Jackson 2009 + Raworth 2017 are the mass-audience landmarks.
- **new_keynesian = 1985** — a rough synthesis date. No single landmark; Mankiw/Romer/Taylor period. Alternative: 1988 (Mankiw-Romer NK microfoundations volume).
- **institutionalism = 1990** (North, *Institutions, Institutional Change and Economic Performance*) — anchors New Institutional Economics. Alternative: 1937 (Coase "Nature of the Firm") if we want the Coase-Williamson-North lineage from the start.
- **mmt = 1996** (Mosler, *Soft Currency Economics*).
- **eco_socialist = 2000** (Foster, *Marx's Ecology*). Alternative: 2007 (Löwy's manifesto).
- **empirical_pragmatist = 2007** (Rodrik, *One Economics, Many Recipes*) — the framework's house position, dated to the clearest methodological articulation.

### Spectrum x values

The axis is "market primacy ↔ state/collective primacy" — it is not normative. Main judgment calls:

- **ordoliberal at +0.50**: markets-with-rules. Higher than `empirical_pragmatist` (+0.25) because ordoliberal is explicitly committed to markets-as-default whereas pragmatist is conditional.
- **developmentalism at −0.10**: markets-embraced-but-state-led. Sits left of mainstream and right of Keynesian heterodoxy. Debatable whether this should be −0.2 or 0.
- **democratic_socialist at −0.70** and **degrowth at −0.70**: tied, for different reasons — democratic-socialist is ownership-reform left; degrowth is growth-skeptical left. They're left-of-centre on the market-primacy axis to comparable degrees but for incompatible reasons. The single-axis map necessarily loses this; the vertical (time) axis or the family colour does the remaining work.
- **marxian vs marxist_leninist** (−0.90 vs −0.95): thin distinction on the state-vs-market axis; the real difference is revolutionary-vs-analytical and is carried by the parent/anti-link structure rather than spectrum_x.

### Parent / anti-link assumptions worth flagging

- **new_keynesian parent = [post_keynesian, chicago_monetarism]**: NK is explicitly the *synthesis*. Listed post-K first because the sticky-price-Keynesian core is more load-bearing than the monetarist rationality incorporation; could be flipped.
- **developmentalism parent = post_keynesian**: Prebisch engaged structuralist demand-side thinking; the real parents (Keynes himself, Friedrich List, German Historical School) are not in our 17. Post-Keynesian is the closest neighbour in-taxonomy. If this feels wrong, the alternative is leaving developmentalism parentless (root).
- **eco_socialist parent = [marxian, degrowth]**: Foster/Klein are explicitly Marxian; degrowth is secondary. If Klein's *This Changes Everything* is the landmark, degrowth arguably moves to primary — you tell me.
- **post_keynesian anti-links = [chicago_monetarism, new_keynesian]**: Kaldor *Scourge of Monetarism* is explicit on the first. On new_keynesian, PK accuses NK of "bastard Keynesianism" — is real but is a more internecine fight than an anti-link. Could be dropped.
- **democratic_socialist anti-link marxist_leninist**: Bernstein-Lenin was a live inter-socialist dispute from 1899 onward. Clear anti-link.
- **austrian anti-link marxist_leninist**: Mises 1920 calculation paper. Clear anti-link.
- **market_socialist anti-link austrian**: Lange was responding to Mises-Hayek. Clear anti-link. (Note: `market_socialist.parent = marxian`, `market_socialist.anti = austrian` — both arrows.)

### Positions with empty arrays

- **classical_liberal**: no parents (root), no anti-links (it is what everything else replies to).
- **institutionalism**, **empirical_pragmatist**, **social_democratic**: no anti-links. These are synthetic/pragmatic positions; they don't define themselves primarily against any one school.
- **marxian** has no parent in our taxonomy (root alongside classical_liberal). Its intellectual parents are Hegel, Smith, Ricardo themselves; all either not in our list or its anti-link.
- **post_keynesian** parent is empty. Keynes himself is not in our 17 — treating PK as a taxonomy root mirrors the marxian treatment.

## What this unlocks for rendering

With these fields in place:

1. **Tier 1 — Positions map**: 17 nodes, vertical axis = `origin_year`, horizontal = `spectrum_x`, colour = `family`. Solid arrows = parent primary (first entry of `parent_position_ids`), dashed arrows = parent secondary (subsequent entries), red anti-link arrows = `anti_link_ids`.
2. **Tier 2 — Movement constellation**: when a position is clicked, all movements with `position_alignments` pointing to it spread out by `timeframe.start` (horizontal) × country region (vertical), coloured by `alignment ∈ {aligned, partially_aligned}`.
3. **Tier 3 — Policies drawer**: when a movement is clicked, its `policies[]` render as a musicmap-style playlist panel with each policy's axis signature as the "track info."

No changes needed to `movement` or `policy` schemas for tiers 2 and 3 — the existing `timeframe`, `position_alignments`, and `policies[]` fields are sufficient. The `reaction_to_movement_id` field floated earlier (Thatcher ↔ 1970s Labour) is a separate enrichment worth doing but is not required for a first pass.

## Next decision point

Before any rendering work, accept / adjust / reject:

1. Are the **7 families** right, or should any be split or merged?
2. Any **origin years** to adjust? (`austrian`, `post_keynesian`, `institutionalism`, `social_democratic`, and `degrowth` are the most contestable.)
3. Any **parent / anti-link** arrows that are wrong or missing?
4. **Spectrum_x** — is the "market primacy" framing the right single axis, or should it be something else (e.g., "redistribution intensity", "anti-growth posture")?

Once these are settled, rendering can proceed without the schema moving under us.
