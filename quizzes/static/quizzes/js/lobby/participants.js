const lobby = document.querySelector(".lobby")
const participantsList = document.querySelector(".participants-list")
const participantsCount = document.querySelector(".count-participants")
const statusCount = document.querySelector(".status-count")

const roomId = lobby.dataset.roomId
const avatarUrl = participantsList.dataset.avatar

const protocol = window.location.protocol === "https:" ? "wss" : "ws"
const ROOM_URL = `${protocol}://${window.location.host}/ws/quizzes/room/${roomId}/`

const roomSocket = new WebSocket(ROOM_URL)

function createParticipantCard(participant) {
  const card = document.createElement("div")
  card.classList.add("recipient")

  const avatar = document.createElement("img")
  avatar.classList.add("recipient-avatar")
  avatar.src = avatarUrl
  avatar.alt = participant.name

  const name = document.createElement("p")
  name.classList.add("recipient-name")
  name.textContent = participant.name

  const status = document.createElement("div")
  status.classList.add("recipient-status")

  const circle = document.createElement("div")
  circle.classList.add("status-circle")

  const statusText = document.createElement("span")
  statusText.classList.add("status-text")
  statusText.textContent = "У кімнаті"

  status.appendChild(circle)
  status.appendChild(statusText)

  card.appendChild(avatar)
  card.appendChild(name)
  card.appendChild(status)

  return card
}

function renderParticipants(participants) {
  participantsList.innerHTML = ""

  participants.forEach((participant) => {
    participantsList.appendChild(createParticipantCard(participant))
  })

  participantsCount.textContent = participants.length
  if (statusCount) {
    statusCount.textContent = participants.length
  }
}

roomSocket.onmessage = function (event) {
  const data = JSON.parse(event.data)

  if (data.action == "participants") {
    renderParticipants(data.participants)
  }
}