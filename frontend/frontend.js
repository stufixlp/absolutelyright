async function fetchToday(animate = false) {
	try {
		const res = await fetch("/api/today");
		const data = await res.json();
		const countElement = document.getElementById("today-inline");
		const subtitleElement = document.querySelector(".subtitle");
		const rightCountElement = document.getElementById("right-count");

		// Update right count display
		if (data.right_count && data.right_count > 0) {
			rightCountElement.textContent = `(+ ${data.right_count} times I was just "right")`;
			rightCountElement.style.display = "block";
		} else {
			rightCountElement.style.display = "none";
		}

		if (animate && data.count > 0) {
			// Show count - 1 first
			countElement.textContent = data.count - 1;

			// Fade in the subtitle
			subtitleElement.style.transition = "opacity 0.5s ease-in";
			subtitleElement.style.opacity = "1";

			// After a second, animate to the real count
			setTimeout(() => {
				countElement.style.transform = "scale(1.3)";
				countElement.style.color = "#e63946";
				countElement.textContent = data.count;

				// Reset the scale
				setTimeout(() => {
					countElement.style.transform = "";
				}, 300);
			}, 1000);
		} else {
			countElement.textContent = data.count;
			// Fade in for non-animated load
			subtitleElement.style.transition = "opacity 0.5s ease-in";
			subtitleElement.style.opacity = "1";
		}
	} catch (error) {
		console.error("Error fetching today:", error);
	}
}

async function fetchHistory() {
	try {
		const res = await fetch("/api/history");
		const history = await res.json();

		// Add today if it's not in the history
		const today = new Date().toISOString().split("T")[0];
		const hasToday = history.some((d) => d.day === today);

		if (!hasToday) {
			// Fetch today's count to add to the chart
			const todayRes = await fetch("/api/today");
			const todayData = await todayRes.json();
			history.push({
				day: today,
				count: todayData.count || 0,
				right_count: todayData.right_count || 0,
			});

			// Sort by date to ensure chronological order
			history.sort((a, b) => a.day.localeCompare(b.day));
		}

		currentHistory = history; // Store for resize
		drawChart(history);
	} catch (error) {
		console.error("Error fetching history:", error);
	}
}

function drawChart(history) {
	const chartElement = document.getElementById("chart");
	chartElement.innerHTML = "";

	if (history.length === 0) return;

	// Make chart dimensions responsive
	const isMobile = window.innerWidth <= 600;
	const containerWidth = Math.min(window.innerWidth - 40, 760);
	const width = containerWidth;
	const height = isMobile ? 300 : 350;

	// Create container div for roughViz
	const container = document.createElement('div');
	container.id = 'chart-container';
	chartElement.appendChild(container);
	
	// On mobile, show only last 5 days
	const displayHistory = isMobile && history.length > 5 
		? history.slice(-5) 
		: history;

	// Prepare data in the format roughViz expects for stacked bars
	const data = displayHistory.map((d, i) => {
		const date = new Date(d.day);
		// Show simplified labels on mobile since we have fewer bars
		const label = isMobile
			? date.toLocaleDateString("en-US", { month: "numeric", day: "numeric" })
			: date.toLocaleDateString("en-US", { month: "short", day: "numeric" });

		return {
			date: label,
			'Absolutely right': d.count,
			'Just right': d.right_count || 0
		};
	});

	if (typeof roughViz === 'undefined') {
		console.error('roughViz library not loaded!');
		return;
	}
	
	new roughViz.StackedBar({
		element: '#chart-container',
		data: data,
		labels: 'date',
		width: width,
		height: height,
		highlight: ['coral', 'skyblue'],
		roughness: 1.5,
		font: 'Gaegu',
		xLabel: '',
		yLabel: isMobile ? '' : 'Times Right',
		interactive: true,
		tooltipFontSize: '0.95rem',
		margin: isMobile
			? { top: 20, right: 10, bottom: 60, left: 40 }
			: { top: 30, right: 20, bottom: 70, left: 80 },
		axisFontSize: isMobile ? '10' : '12',
		axisStrokeWidth: isMobile ? 1 : 1.5,
		strokeWidth: isMobile ? 1.5 : 2,
	});
}

// Store history globally for redraw
let currentHistory = [];

// Load roughViz library
const script = document.createElement('script');
script.src = 'https://unpkg.com/rough-viz@2.0.5';
script.onload = () => {
	// Initial load with animation
	fetchToday(true);
	fetchHistory().then(() => {
		// Redraw chart on window resize
		let resizeTimeout;
		window.addEventListener("resize", () => {
			clearTimeout(resizeTimeout);
			resizeTimeout = setTimeout(() => {
				if (currentHistory.length > 0) {
					drawChart(currentHistory);
				}
			}, 250);
		});
	});
};
document.head.appendChild(script);

// Refresh every 5 seconds (without animation)
setInterval(() => fetchToday(false), 5000);