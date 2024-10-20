console.log("js")

await fetch("file.csv")
    .then((res) => res.text())
    .then((text) => console.log(text))
    .catch((e) => console.error(e));