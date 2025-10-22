
const monthYear = document.getElementById("monthYear");
const calendarDays = document.getElementById("calendarDays");
const prevMonthBtn = document.getElementById("prevMonth");
const nextMonthBtn = document.getElementById("nextMonth");

const months = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
];

let currentDate = new Date();

function renderCalendar() {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    monthYear.textContent = `${months[month]} ${year}`;
    const firstDay = new Date(year, month, 1).getDay();
    const lastDate = new Date(year, month + 1, 0).getDate();
    const prevLastDate = new Date(year, month, 0).getDate();
    calendarDays.innerHTML = "";
    for (let i = firstDay - 1; i >= 0; i--) {
        const div = document.createElement("div");
        div.textContent = prevLastDate - i;
        div.className = "text-gray-400";
        calendarDays.appendChild(div);
    }
    for (let i = 1; i <= lastDate; i++) {
        const div = document.createElement("div");
        
        div.textContent = i;
        const today = new Date();
        if (
            i === today.getDate() &&
            month === today.getMonth() &&
            year === today.getFullYear()
        ) {
            div.className = "font-semibold text-blue-500";
        } else {
            div.className = "hover:bg-blue-100 rounded-full transition";
        }

        calendarDays.appendChild(div);
    }
    const totalCells = firstDay + lastDate;
    const nextDays = 7 - (totalCells % 7);
    if (nextDays < 7) {
        for (let i = 1; i <= nextDays; i++) {
            const div = document.createElement("div");
            div.textContent = i;
            div.className = "text-gray-400";
            calendarDays.appendChild(div);
        }
    }
}
prevMonthBtn.addEventListener("click", () => {
    currentDate.setMonth(currentDate.getMonth() - 1);
    renderCalendar();
});

nextMonthBtn.addEventListener("click", () => {
    currentDate.setMonth(currentDate.getMonth() + 1);
    renderCalendar();
});
renderCalendar();