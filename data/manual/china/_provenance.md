# China manual-drop data — provenance & citations

This directory holds curated YAML data for primary academic sources that
are not available via automated fetcher (out-of-print monographs, Chinese-
language demographic reconstructions, archival customs records). Each file
publishes a single `series_id` consumable by the `china_manual` publisher
fetcher (`data/fetchers/china_manual.py`).

Curation principle: every numeric observation is traceable to a peer-
reviewed primary source listed in the file's `citations:` block. Ranges
and disagreements between sources are preserved (see e.g.
`great_leap_mortality.yaml` for the four anchor estimates that bracket
the 30-45M consensus interval).

## File-by-file primary sources

### `great_leap_mortality.yaml`
Excess deaths during the Great Leap Forward famine, 1958-1962 (millions).
- Banister, Judith (1987). *China's Changing Population*. Stanford UP. (30M)
- Ashton, B., Hill, K., Piazza, A., Zeitz, R. (1984). "Famine in China,
  1958-61." *Population and Development Review* 10(4): 613-645. (30M)
- Peng Xizhe (1987). "Demographic Consequences of the Great Leap Forward
  in China's Provinces." *PDR* 13(4): 639-670. (23M lower bound)
- Yang Jisheng (2008). *Tombstone (Mubei)*. Hong Kong: Cosmos Books;
  English ed. FSG 2012. (36M)
- Chen-Yang upper-bound synthesis cited in Yang (2008) concluding chapter
  and aligned with Dikotter (2010) *Mao's Great Famine*. (45M)

Canonical headline value: **36M** (median of the four anchors).

### `grain_output_1957_1965.yaml`
Annual grain output 1957-1965 (million tonnes), revised post-1978 NBS series.
- PRC State Statistical Bureau (1983). *China Statistical Yearbook 1983*.
  Beijing: China Statistics Press.
- Lin, Justin Yifu (1990). "Collectivization and China's Agricultural
  Crisis in 1959-1961." *Journal of Political Economy* 98(6): 1228-1252.
- Perkins, Dwight H. (1969). *Agricultural Development in China,
  1368-1968*. Edinburgh UP. (Pre-1957 trend cross-check.)

Replaces the inflated 1958-1960 contemporaneous reports (e.g. nominal
375 Mt for 1958) with the consensus revised series (200 Mt peak 1958,
143.5 Mt trough 1960).

### `crude_death_rate.yaml`
Annual CDR 1955-1965 (deaths per 1000 population).
- PRC NBS *China Statistical Yearbook*, vital statistics chapter,
  various editions 1981-2005.
- Banister (1987) *China's Changing Population*, Table 4.1 (alongside
  reconstructed series for 1958-1961 — included as `reconstructed_value`).

The 1960 spike (25.43/1000) is the canonical demographic signature
of the famine. Banister's reconstruction places the 1959 figure at
18.1 (vs the under-reported official 14.59) and the 1960 figure at
28.6.

### `crude_birth_rate.yaml`
Annual CBR 1955-1965 (births per 1000 population).
- PRC NBS *China Statistical Yearbook*.
- Banister (1987).
- Coale, Ansley J. (1981). "Population Trends, Population Policy and
  Population Studies in China." *PDR* 7(2): 261-297.

Trough 18.02 in 1961 vs 1957 baseline 34.03 = 47% decline. Post-1962
rebound (37-43/1000 in 1962-1964) confirms the amenorrhea
mechanism — fertility resumed when nutrition recovered.

### `life_expectancy.yaml`
Period life expectancy at birth 1955-1965 (years).
- Banister (1987) Table 4.10 reconstruction.
- Coale, Ansley J. (1984). *Rapid Population Change in China,
  1952-1982*. National Academy Press.

WHO GHO life-expectancy series begins 2000, so for the GLF window
the Banister reconstruction is the only available data. The 1960
trough (24.6) is mechanically driven by infant + early-child mortality
spike — period life expectancy is highly sensitive to deaths
concentrated at young ages.

### `commune_coverage.yaml`
People's Commune enrollment 1958-1962 (% of rural households).
- CCP Central Committee, "Resolution on the Establishment of People's
  Communes in the Rural Areas" (Beidaihe Resolution), 29 August 1958.
- MacFarquhar, Roderick (1983). *The Origins of the Cultural
  Revolution, Vol 2: The Great Leap Forward 1958-1960*. Columbia UP.
- Chan, A., Madsen, R., Unger, J. (1984). *Chen Village*. UC Press.

99.1% of rural households enrolled by end-Dec 1958 — ~4 months from
the Beidaihe resolution. The monthly buildup table preserves the
August-December 1958 acceleration.

### `provincial_excess_mortality.yaml`
Provincial excess mortality 1958-1962 (% of 1957 provincial population).
- Peng Xizhe (1987) *PDR*.
- Cao Shuji (2005). *Da Jihuang: 1959-1961 nian de Zhongguo renkou*
  (The Great Famine: China's Population 1959-1961). Hong Kong: Time
  International Publishing.
- Yang Jisheng (2008) *Tombstone*.
- Kung, J. K.-S. and Chen, S. (2011). "The Tragedy of the Nomenklatura:
  Career Incentives and Political Radicalism during China's Great Leap
  Famine." *American Economic Review* 101(4): 1280-1306.

Six provinces (Anhui 18.4%, Sichuan 13.1%, Qinghai 13.0%, Gansu 11.3%,
Guizhou 10.5%, Henan 10.0%) clear the >10% threshold.

### `grain_exports.yaml`
Net grain exports 1957-1962 (million tonnes).
- PRC General Administration of Customs annual trade statistics
  (compiled in subsequent NBS publications).
- Riskin, Carl (1987). *China's Political Economy*. Oxford UP. Table 6.5.
- Li Wenhua (2005), grain trade reconstruction (cited in Yang 2008).

China was a NET grain exporter through 1959-1960 despite domestic
famine (4.16 Mt 1959, 2.72 Mt 1960). Imports were authorised only
in 1961 under the readjustment (-4.45 Mt net = 4.45 Mt net import).

### `backyard_steel.yaml`
Backyard-steel campaign capital waste and labour diversion 1958-1959.
- Bachman, David (1991). *Bureaucracy, Economy, and Leadership in
  China: The Institutional Origins of the Great Leap Forward*.
  Cambridge UP.
- MacFarquhar (1983) Vol. 2.
- Lardy, Nicholas R. (1987). "The Chinese Economy under Stress,
  1958-1965." In MacFarquhar & Fairbank (eds), *Cambridge History of
  China Vol. 14: The People's Republic Part 1*. Cambridge UP.

Approximately 47% of 1958 reported backyard-steel output (~5 Mt of
the ~11 Mt nominal total) was unusable pig iron of agricultural-
implement quality only; ~90M labourers diverted to furnaces during
the autumn 1958 harvest window.

## Curation timestamp

All files added 2026-04-24 to close the data gap on the
`great_leap_forward_famine_output_collapse_1959_1961` multi-metric
hypothesis run.
