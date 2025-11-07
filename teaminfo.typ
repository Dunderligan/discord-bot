#let ratio =  1  * 16/9
#let height = 540pt
#set page(
  height: height,
  width: height * ratio,
  margin: 32pt
)
#set text(
  font: "Rajdhani",
  size: 18pt,
  fill: rgb("#1f2937")
)

#show heading.where(level: 1): set text(size: 50pt, font: "Inter 28pt", weight: "semibold")
#show heading.where(level: 2): set text(size: 30pt, font: "Inter 28pt", weight: "semibold", style: "italic")

#show table.cell.where(y: 0): set text(weight: "bold")

#let document_data = ("standings": (("placeholder-team.jpg", "Omedvetna Pappertussarna", "9/0/0", "9p"), ("team_thumbnails/d1c84e6b-caa5-4ee1-bc83-0cb1eeac1365.png", "Cool Sharks", "9/0/0", "9p"), ("placeholder-team.jpg", "Oklippta Gamers", "6/3/0", "6p"), ("team_thumbnails/f5b97a04-de2a-4d7d-94ba-952c8ec61701.png", "Flexibla Björnarna", "6/3/0", "6p"), ("placeholder-team.jpg", "Läskiga Hajarna", "3/6/0", "3p"), ("team_thumbnails/eeb86332-2d0a-4668-9c5c-97f5edc4ce5e.png", "Mogna Pojkarna", "3/6/0", "3p"), ("placeholder-team.jpg", "Rika Gamers", "0/9/0", "0p"), ("placeholder-team.jpg", "Starka Pappertussarna", "0/9/0", "0p")), "division": 1, "season": "7")
//#let document_data = json(bytes(sys.inputs.document_data))
#grid(
    columns: (auto, auto, auto, 1fr),
    align: (left + horizon, left+horizon, left,right+horizon),
    [== DIVISION 1],
    h(10pt),
    grid.cell(
      rowspan: 2,
      image("logo.png", width: 100pt),
    ),
    image("dl_logo.png", height: 50pt),
    [= COOL SHARKS]
  )
#v(1fr)

#let image_size = 32pt
/*#table(
  columns: (auto, 1fr, auto, auto),
  stroke: none,
  inset: ("x": 8pt, "y": 0pt),
  align: (horizon+center, horizon, horizon+center, horizon+center),
  fill: (_, y) => if y > 0 {rgb("#e5e7eb")},
  row-gutter: 8pt,
  table.header(
    [Lag], [], [W/L/D], [Poäng]
  ),
  ..for (team_logo, team, result, points) in document_data.at("standings") {
    (image(team_logo, height: image_size, width: image_size), team, result, points)
  }
)*/
#let players = table(
  columns: (auto, auto, auto, auto, auto),
  stroke: none,
  inset: ("x": 16pt, "y": 8pt),
  align: center,
  fill: (_, y) => if y > 0 {rgb("#e5e7eb")},
  row-gutter: 8pt,
  table.header(
    [Roll], [Rank], [], [Battletag], []
  ),
  ..for (role, rank, tier, battletag, captain) in (("dps", "diamond", "1", "StarkeAdrian#12323", ""), ("dps", "diamond", "1", "StarkeAdrian#12323", "Captain"),("dps", "diamond", "1", "StarkeAdrian#12323", ""),("dps", "diamond", "1", "StarkeAdrian#12323", ""),("dps", "diamond", "1", "StarkeAdrian#12323", ""),("dps", "diamond", "1", "StarkeAdrian#12323", ""),("dps", "diamond", "1", "StarkeAdrian#12323", ""),)
  {
    (role, rank, tier, battletag, captain)
  }
)

#grid(
  columns: (1fr, auto),
  align: (left, right),
  players,
  grid(
    columns: (auto),
    row-gutter: 16pt,
    inset: 12pt,
    [== Tidigare matcher],
    grid.cell(
      fill: rgb("#a2e787"),
      [3-0 vs. Tjocka Apgänget]
    ),
    grid.cell(
      fill: rgb("#cf6666"),
      [1-2 vs. Ocustik]
    ),
    grid.cell(
      fill: rgb("#cf6666"),
      [0-3 vs. Ragge och hans coola lag]
    ),
  )
)
#v(1fr)

#let current_time = "2025-11-03, 18.04"
//#let current_time = json(bytes(sys.inputs.time))
#grid(
  columns: (auto, auto, auto),
  [\@Dunderligan],
  [#h(1fr)],
  [*Spelade säsonger:* S7, S6, S5, S3, S1]
)