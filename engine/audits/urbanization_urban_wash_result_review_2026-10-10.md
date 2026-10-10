# Urban WASH family: post-result review

Blind first-addition registration `db01518329bc83746f9d915cbbc88a97c5194cc9`
preceded separately committed exact-source lock
`9d56b92325495b4c21b3ea33da4ae07d5fbace97`. The selected WHO values
were first opened after both commits. All three original outcomes and gates
were retained. Exact source-hash checks and `--verify` replay passed using
`--source-root <local raw cache>` against the ignored pinned source files.

| Frozen urban outcome | Result | Complete rows / countries | Beta per +1 urban-share point | Two-sided p | Gate disposition |
| --- | --- | ---: | ---: | ---: | --- |
| Safely managed drinking water | **INCONCLUSIVE** | 486 / 99 | Not estimated | Not estimated | One country's residualized exposure weight is 16.50%, over the frozen 15% cap; archive. |
| Safely managed sanitation | **PARTIAL** | 590 / 120 | −0.0826402 | 0.390339 | All frozen gates pass; public descriptive calibration. |
| At-least-basic drinking water | **PARTIAL** | 850 / 174 | +0.0461090 | 0.0105566 | All frozen gates pass, but p exceeds the family cutoff `0.01/3` and magnitude is below 0.2; public descriptive calibration. |

An independent least-squares plus country-cluster sandwich calculation on
the frozen complete-case panels reproduced both published coefficients and
standard errors to numerical tolerance: sanitation `−0.0826401800967117`,
`0.09585356184224136`; basic water `+0.046109042120939595`,
`0.017835849139412708`. The result packets and their exact-replay check are
under the three `engine/runs/urbanization_urban_*_forward_2026/` directories.

These **two** gate-cleared packets are one correlated descriptive family, not
two policy effects or causal confirmations. The safely managed water packet
does not graduate, even though its coverage is complete. The WHO/JMP data are
adjusted/predicted estimates; inference can reflect shared source trends and
country classification changes. Their manifest records
`CC-BY-NC-SA-3.0 IGO`, so external publication of any derived display
remains subject to source-rights review. No raw WHO file entered Git.
