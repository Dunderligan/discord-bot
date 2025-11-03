#set page(
  height: 500pt,
  width: 500pt,
  margin: 15pt
)
#set text(
  font: "Rajdhani",
  size: 18pt,
  fill: rgb("#1f2937")
)

#show heading.where(level: 1): set text(size: 40pt, font: "Inter 28pt", weight: "semibold")
#show heading.where(level: 2): set text(size: 26pt, font: "Inter 28pt", weight: "semibold", style: "italic")

#show table.cell.where(y: 0): set text(weight: "bold")

//#let document_data = ("standings": (("Omedvetna Pappertussarna", "9/0/0", "9p"), ("Cool Sharks", "9/0/0", "9p"), ("Oklippta Gamers", "6/3/0", "6p"), ("Flexibla Björnarna", "6/3/0", "6p"), ("Läskiga Hajarna", "3/6/0", "3p"), ("Mogna Pojkarna", "3/6/0", "3p"), ("Rika Gamers", "0/9/0", "0p"), ("Starka Pappertussarna", "0/9/0", "0p")), "division": 1, "season": "7")
#let document_data = json(bytes(sys.inputs.document_data))
#grid(
  columns: (1fr, auto),
  align: (left + horizon, right+horizon),
  [= STÄLLNING],
  image("dl_logo.png", height: 50pt),
  [== SÄSONG #document_data.at("season") - DIVISION #document_data.at("division")]
)
#v(1fr)

#table(
  columns: (auto, 1fr, auto, auto),
  stroke: none,
  align: (horizon+center, horizon, horizon+center, horizon+center),
  fill: (_, y) => if y > 0 {rgb("#e5e7eb")},
  row-gutter: 6pt,
  table.header(
    [Lag], [], [W/L/D], [Poäng]
  ),
  ..for (team_logo, team, result, points) in document_data.at("standings") {
    (image(team_logo, height: 24pt), team, result, points)
  }
)
#v(1fr)

//#let current_time = "2025-11-03, 18.04"
#let current_time = json(bytes(sys.inputs.time))
\@Dunderligan - Uppdaterad #current_time