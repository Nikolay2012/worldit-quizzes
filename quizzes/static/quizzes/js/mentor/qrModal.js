const qrButton = document.querySelector(".show-qr")
const qrModal = document.getElementById("qrModal")

qrButton.addEventListener("click", () => {
    openModal(qrModal)
})