const startForm = document.querySelector(".start-form")
const statusRoom = document.querySelector(".status-room")


const csrfToken = document.querySelector("meta[name='csrf-token']").content

startForm.addEventListener("submit", async (event) => {
    event.preventDefault()

    const response = await fetch(startForm.action, {
        method: "POST",
        headers: { "X-CSRFToken": csrfToken },
    })

    const data = await response.json()

    if (data.success) {
        window.location.href = data.url
    } else {
        statusRoom.classList.remove("green")
        statusRoom.textContent = data.message
    }
})