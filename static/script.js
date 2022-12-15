let trans_container = document.getElementById("transactions_container");

let chooser = document.querySelector("select[name='transactions']");
// console.dir(chooser.value);

let state;

document.addEventListener("change", (event) => {
  if (event.target.name === "transactions") {
    displayStatus = event.target.value;
    if (displayStatus === "sold") {
      // console.log('sold')
      state = 'sold'
    } else {
      // console.log('bought')
      state = 'bought'
    }
  }
});

