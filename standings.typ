#set page(
  height: 500pt,
  width: 500pt,
  margin: 15pt
)
#set text(
  font: "Rajdhani",
  size: 18pt
)

#show heading.where(level: 1): set text(size: 40pt)
#show heading.where(level: 2): set text(size: 30pt)

#show table.cell.where(y: 0): set text(weight: "bold")

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
  fill: (_, y) => if y > 0 {rgb("eceaf2")},
  row-gutter: 6pt,
  table.header(
    [Lag], [], [W/L/D], [Poäng]
  ),
  ..for (team, result, points) in document_data.at("standings") {
    (image("logo.png", height: 24pt), team, result, points)
  }
)
#v(1fr)

#let current_time = json(bytes(sys.inputs.time))
\@ Dunderligan - Uppdaterad #current_time