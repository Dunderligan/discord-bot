#let ratio =  1  * 16/9
#let height = 540pt
#set page(
  height: height,
  width: height * ratio,
  margin: 24pt
)
#set text(
  font: "Rajdhani",
  size: 18pt,
  fill: rgb("#1f2937")
)

#show heading.where(level: 1): set text(size: 40pt, font: "Inter 28pt", weight: "semibold")
#show heading.where(level: 2): set text(size: 26pt, font: "Inter 28pt", weight: "semibold", style: "italic")

#show table.cell.where(y: 0): set text(weight: "bold")

#let document_data = ("standings": (("placeholder-team.jpg", "Omedvetna Pappertussarna", "9/0/0", "9p"), ("team_thumbnails/d1c84e6b-caa5-4ee1-bc83-0cb1eeac1365.png", "Cool Sharks", "9/0/0", "9p"), ("placeholder-team.jpg", "Oklippta Gamers", "6/3/0", "6p"), ("team_thumbnails/f5b97a04-de2a-4d7d-94ba-952c8ec61701.png", "Flexibla Björnarna", "6/3/0", "6p"), ("placeholder-team.jpg", "Läskiga Hajarna", "3/6/0", "3p"), ("team_thumbnails/eeb86332-2d0a-4668-9c5c-97f5edc4ce5e.png", "Mogna Pojkarna", "3/6/0", "3p"), ("placeholder-team.jpg", "Rika Gamers", "0/9/0", "0p"), ("placeholder-team.jpg", "Starka Pappertussarna", "0/9/0", "0p")), "division": 1, "season": "7")
//#let document_data = json(bytes(sys.inputs.document_data))
#grid(
  columns: (1fr, auto),
  align: (left + horizon, right+horizon),
  [= STÄLLNING],
  image("dl_logo.png", height: 50pt),
  [== SÄSONG #document_data.at("season") - DIVISION #document_data.at("division")]
)
#v(1fr)

#let image_size = 32pt
#table(
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
)
#v(1fr)

#let current_time = "2025-11-03, 18.04"
//#let current_time = json(bytes(sys.inputs.time))
\@Dunderligan - Uppdaterad #current_time