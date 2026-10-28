const copyBtn = document.querySelector(".copy-code")
const joinData = document.querySelector(".join-data")

async function copyToClipboard(text) {
  try {
    await navigator.clipboard.writeText(text)
  } catch (error) {
    console.log(error)
  }
}

copyBtn.addEventListener("click",async () => {
    const roomCode = joinData.dataset.code
    await copyToClipboard(roomCode)
})