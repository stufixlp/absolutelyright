  // Load rough.js
  import rough from 'https://unpkg.com/roughjs@4.5.2/bundled/rough.esm.js';

  async function fetchToday(animate = false) {
    try {
      const res = await fetch("/api/today");
      const data = await res.json();
      const countElement = document.getElementById("today");
      const subtitleElement = document.querySelector(".subtitle");
      const rightCountElement = document.getElementById("right-count");
      
      // Update right count display
      if (data.right_count && data.right_count > 0) {
        rightCountElement.textContent = `+ ${data.right_count} times just "right"`;
        rightCountElement.style.display = 'block';
      } else {
        rightCountElement.style.display = 'none';
      }
      
      if (animate && data.count > 0) {
        // Show count - 1 first WITHOUT pulsating
        countElement.classList.remove('pulsating');
        countElement.textContent = data.count - 1;
        
        // Fade in the elements
        countElement.style.transition = 'opacity 0.5s ease-in';
        subtitleElement.style.transition = 'opacity 0.5s ease-in';
        countElement.style.opacity = '1';
        subtitleElement.style.opacity = '1';
        
        // After a second, animate to the real count
        setTimeout(() => {
          countElement.style.transform = 'scale(1.2)';
          countElement.textContent = data.count;
          
          // Reset the scale and start pulsating
          setTimeout(() => {
            countElement.style.transform = '';
            countElement.classList.add('pulsating');
          }, 300);
        }, 1000);
      } else {
        countElement.textContent = data.count;
        countElement.classList.add('pulsating');
        // Fade in for non-animated load
        countElement.style.transition = 'opacity 0.5s ease-in';
        subtitleElement.style.transition = 'opacity 0.5s ease-in';
        countElement.style.opacity = '1';
        subtitleElement.style.opacity = '1';
      }
    } catch (error) {
      console.error("Error fetching today:", error);
    }
  }

  async function fetchHistory() {
    try {
      const res = await fetch("/api/history");
      const history = await res.json();
      console.log("History data:", history);
      currentHistory = history; // Store for resize
      drawChart(history);
    } catch (error) {
      console.error("Error fetching history:", error);
    }
  }

  function drawChart(history) {
    const svg = document.getElementById("chart");
    svg.innerHTML = "";

    if (history.length === 0) return;

    // Make chart dimensions responsive
    const containerWidth = Math.min(window.innerWidth - 40, 800);
    const isMobile = window.innerWidth <= 600;
    const w = containerWidth;
    const h = isMobile ? 250 : 300;
    
    // Update SVG viewBox to match actual dimensions
    svg.setAttribute("viewBox", `0 0 ${w} ${h}`);
    
    const padding = isMobile 
      ? { top: 30, right: 20, bottom: 50, left: 50 }
      : { top: 40, right: 60, bottom: 60, left: 100 };
    const chartWidth = w - padding.left - padding.right;
    const chartHeight = h - padding.top - padding.bottom;
    const max = Math.max(...history.map(d => d.count)) || 10;
    const stepX = chartWidth / (history.length - 1 || 1);

    // Initialize rough.js
    const rc = rough.svg(svg);

    // Add white background with sketchy border
    const bgRect = rc.rectangle(5, 5, w - 10, h - 10, {
      fill: 'white',
      fillStyle: 'solid',
      stroke: '#d0d7de',
      strokeWidth: 1.5,
      roughness: 1.2
    });
    svg.appendChild(bgRect);

    // Draw horizontal grid lines with hand-drawn style
    const yTicks = 6;
    for (let i = 0; i <= yTicks; i++) {
      const y = padding.top + (chartHeight / yTicks) * i;
      const isBaseline = i === yTicks;
      
      const line = rc.line(
        padding.left, y,
        w - padding.right, y,
        {
          stroke: isBaseline ? '#6b7280' : '#e5e7eb',
          strokeWidth: isBaseline ? 1.5 : 0.8,
          roughness: 0.8,
          bowing: 0.5
        }
      );
      svg.appendChild(line);
    }

    // Draw vertical axis
    const yAxis = rc.line(
      padding.left, padding.top,
      padding.left, padding.top + chartHeight,
      {
        stroke: '#6b7280',
        strokeWidth: 1.5,
        roughness: 0.8,
        bowing: 0.3
      }
    );
    svg.appendChild(yAxis);

    // Prepare data points
    const points = history.map((d, i) => ({
      x: padding.left + i * stepX,
      y: padding.top + chartHeight - (d.count / max) * chartHeight,
      count: d.count,
      day: d.day
    }));

    // Draw the main line with hand-drawn style
    if (points.length > 1) {
      for (let i = 0; i < points.length - 1; i++) {
        const line = rc.line(
          points[i].x, points[i].y,
          points[i + 1].x, points[i + 1].y,
          {
            stroke: '#e63946',
            strokeWidth: 3,
            roughness: 1.5,
            bowing: 0.8
          }
        );
        svg.appendChild(line);
      }
    }

    // Draw data points as sketchy circles
    points.forEach(point => {
      const circle = rc.circle(point.x, point.y, 10, {
        stroke: '#e63946',
        strokeWidth: 2,
        fill: '#ffffff',
        fillStyle: 'solid',
        roughness: 1.2
      });
      svg.appendChild(circle);

      // Add hover area for tooltip
      const hoverCircle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      hoverCircle.setAttribute("cx", point.x);
      hoverCircle.setAttribute("cy", point.y);
      hoverCircle.setAttribute("r", "8");
      hoverCircle.setAttribute("fill", "transparent");
      hoverCircle.setAttribute("style", "cursor: pointer");
      
      const title = document.createElementNS("http://www.w3.org/2000/svg", "title");
      title.textContent = `${point.day}: ${point.count}`;
      hoverCircle.appendChild(title);
      
      svg.appendChild(hoverCircle);
    });

    // Add Y-axis labels with hand-written style
    for (let i = 0; i <= yTicks; i++) {
      const value = Math.round((max / yTicks) * (yTicks - i));
      const y = padding.top + (chartHeight / yTicks) * i;

      const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
      text.setAttribute("x", padding.left - 15);
      text.setAttribute("y", y + 4);
      text.setAttribute("text-anchor", "end");
      text.setAttribute("font-size", isMobile ? "11" : "14");
      text.setAttribute("fill", "#374151");
      text.setAttribute("font-family", "Kalam, 'Comic Sans MS', 'Marker Felt', cursive");
      text.setAttribute("transform", `rotate(-2, ${padding.left - 15}, ${y + 4})`);
      text.textContent = value >= 1000 ? `${(value/1000).toFixed(1)}k` : value;
      svg.appendChild(text);
    }

    // Y-axis label with hand-written style
    const yLabel = document.createElementNS("http://www.w3.org/2000/svg", "text");
    yLabel.setAttribute("x", 20);
    yLabel.setAttribute("y", padding.top + chartHeight / 2);
    yLabel.setAttribute("transform", `rotate(-90, 20, ${padding.top + chartHeight / 2})`);
    yLabel.setAttribute("text-anchor", "middle");
    yLabel.setAttribute("font-size", isMobile ? "13" : "16");
    yLabel.setAttribute("fill", "#1f2937");
    yLabel.setAttribute("font-family", "Kalam, 'Comic Sans MS', 'Marker Felt', cursive");
    yLabel.textContent = "Times Right";
    svg.appendChild(yLabel);

    // X-axis label with hand-written style
    const xLabel = document.createElementNS("http://www.w3.org/2000/svg", "text");
    xLabel.setAttribute("x", padding.left + chartWidth / 2);
    xLabel.setAttribute("y", h - 10);
    xLabel.setAttribute("text-anchor", "middle");
    xLabel.setAttribute("font-size", isMobile ? "13" : "16");
    xLabel.setAttribute("fill", "#1f2937");
    xLabel.setAttribute("font-family", "Kalam, 'Comic Sans MS', 'Marker Felt', cursive");
    xLabel.textContent = "Date";
    svg.appendChild(xLabel);

    // Add X-axis date labels with slight rotation for hand-written feel
    if (history.length > 0) {
      const xLabelCount = Math.min(6, history.length);
      const xStep = Math.floor((history.length - 1) / (xLabelCount - 1));
      
      for (let i = 0; i < xLabelCount; i++) {
        const idx = i === xLabelCount - 1 ? history.length - 1 : i * xStep;
        const d = history[idx];
        const x = padding.left + idx * stepX;
        
        const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
        text.setAttribute("x", x);
        text.setAttribute("y", h - padding.bottom + 25);
        text.setAttribute("text-anchor", "middle");
        text.setAttribute("font-size", isMobile ? "11" : "13");
        text.setAttribute("fill", "#6b7280");
        text.setAttribute("font-family", "Kalam, 'Comic Sans MS', 'Marker Felt', cursive");
        text.setAttribute("transform", `rotate(${-5 + Math.random() * 10}, ${x}, ${h - padding.bottom + 25})`);
        
        // Format date to show month/day
        const date = new Date(d.day);
        text.textContent = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        svg.appendChild(text);
      }
    }

    // Add a fun doodle or annotation
    const annotation = document.createElementNS("http://www.w3.org/2000/svg", "text");
    annotation.setAttribute("x", w - 100);
    annotation.setAttribute("y", 30);
    annotation.setAttribute("text-anchor", "middle");
    annotation.setAttribute("font-size", isMobile ? "12" : "14");
    annotation.setAttribute("fill", "#9ca3af");
    annotation.setAttribute("font-family", "Kalam, 'Comic Sans MS', 'Marker Felt', cursive");
    annotation.setAttribute("transform", `rotate(5, ${w - 100}, 30)`);
    annotation.textContent = "Perfect!";
    svg.appendChild(annotation);

  }

  // Store history globally for redraw
  let currentHistory = [];

  // Initial load with animation
  fetchToday(true);
  fetchHistory().then(() => {
    // Redraw chart on window resize
    let resizeTimeout;
    window.addEventListener('resize', () => {
      clearTimeout(resizeTimeout);
      resizeTimeout = setTimeout(() => {
        if (currentHistory.length > 0) {
          drawChart(currentHistory);
        }
      }, 250);
    });
  });
  
  // Refresh every 5 seconds (without animation)
  setInterval(() => fetchToday(false), 5000);