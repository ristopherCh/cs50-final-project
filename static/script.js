let trans_container = document.getElementById("transactions_container");

let chooser = document.querySelector("select[name='transactions']");
// console.dir(chooser.value);

let state;

document.addEventListener("change", (event) => {
  if (event.target.name === "transactions") {
    displayStatus = event.target.value;
    // console.log(displayStatus)
    if (displayStatus === "sold") {
      // console.log('sold')
      state = "sold";
      document.querySelector("#bought-items").style.display = "none"
      document.querySelector("#sold-items").style.display = "flex"
    } else {
      // console.log('bought')
      state = "bought";
      document.querySelector("#bought-items").style.display = "flex"
      document.querySelector("#sold-items").style.display = "none"
    }
  }
});

