import styled, { css, keyframes } from "styled-components";
import { useEffect, useRef, useState } from "react";
import {
  Recycle,
  Trash2,
  Leaf,
  BarChart2,
  RefreshCw,
  AlertTriangle,
  BellRing,
} from "lucide-react";

// --- Keyframe Animations ---
const glow = (color) => keyframes`
  0%, 100% { box-shadow: 0 0 5px ${color}, 0 0 5px ${color}; }
  50% { box-shadow: 0 0 5px ${color}, 0 0 10px ${color}; }
`;

const fadeIn = keyframes`
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
`;

// --- General Styled Components ---
const AppWrapper = styled.div`
  background-color: #111827;
  height: 100vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  align-items: center;
  font-family: "Inter", "Arial", sans-serif;
  padding: 2rem;
  color: #f9fafb;
`;

const Header = styled.header`
  width: 100%;
  max-width: 90rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  animation: ${fadeIn} 0.5s ease-out;
  flex-shrink: 0;
`;

const WelcomeMessage = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
  h1 {
    font-size: 2.25rem;
    font-weight: bold;
    margin: 0;
  }
  p {
    font-size: 1.125rem;
    margin: 0;
    color: #9ca3af;
  }
`;

const Logo = styled.div`
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100px;
  height: 100px;
  overflow: hidden;
  box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
  background-color: transparent;

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
`;

const MainContent = styled.div`
  background: #1f2937;
  border-radius: 1.5rem;
  padding: 2rem;
  box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1);
  display: flex;
  flex-direction: column;
`;

const SectionTitle = styled.h2`
  font-size: 1.25rem;
  margin: 0 0 1rem 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #9ca3af;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
`;

const CombinedBody = styled.div`
  display: flex;
  flex-direction: row;
  gap: 2rem;
  width: 100%;
  max-width: 90rem;
  flex-grow: 1;
  animation: ${fadeIn} 0.5s ease-out forwards;
  align-items: stretch;
`;

const SorterColumn = styled(MainContent)`
  flex: 3;
  gap: 1.5rem;
  padding: 1.5rem;
`;

const DashboardColumn = styled(MainContent)`
  flex: 2;
  justify-content: space-around;
  padding: 1.5rem;
`;

const NotifyButton = styled.button`
  background-color: #10b981;
  color: #f9fafb;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 0.75rem;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: background-color 0.2s, transform 0.2s;
  &:hover {
    background-color: #34d399;
    transform: translateY(-2px);
  }
`;

// --- Webcam & Sorter Styles ---
const VideoContainer = styled.div`
  position: relative;
  width: 100%;
  max-width: 600px;
  margin: 0 auto;
  aspect-ratio: 16 / 9;
  background-color: black;
  border-radius: 1rem;
  overflow: hidden;
  margin-bottom: 6rem;
`;

const StyledVideo = styled.video`
  width: 100%;
  height: 100%;
  object-fit: cover;
  position: relative;
  z-index: 2;
  transform: scaleX(-1);
`;

const VideoOverlay = styled.div`
  position: absolute;
  top: 0;
  left: 0;
  z-index: 3;
  width: 100%;
  height: 100%;
  background: rgba(17, 24, 39, 0.75);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #f9fafb;
  font-size: 1.5rem;
  font-weight: bold;
  text-align: center;
`;

// --- COMPONENT FOR CONFIDENCE SCORE ---
const ConfidenceDisplay = styled.div`
  background-color: rgba(0, 0, 0, 0.3);
  padding: 0.5rem 1.25rem;
  border-radius: 9999px; /* Pill shape */
  animation: ${fadeIn} 0.4s ease-out;
  font-weight: bold;
  font-size: 1.125rem;
  /* Use transient prop '$color' to avoid it being passed to the DOM */
  color: ${(props) => props.$color};
  border: 1px solid ${(props) => props.$color};
  box-shadow: 0 0 10px -2px ${(props) => props.$color};
`;

const BinsContainer = styled.div`
  display: flex;
  flex-direction: row;
  justify-content: space-around;
  gap: 1.5rem;
`;

const DroppingArrow = styled.div`
  position: absolute;
  top: -90px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  /* Use transient prop '$color' */
  color: ${(props) => props.$color || "#fff"};
  font-size: 1.8rem;

  span {
    animation: stretch-drop 1.5s ease-out infinite;
    transform-origin: bottom center;
  }

  span:nth-child(2) {
    animation-delay: 0.15s;
  }

  span:nth-child(3) {
    animation-delay: 0.3s;
  }

  @keyframes stretch-drop {
    0% {
      opacity: 0;
      transform: translateY(-30px) scaleY(0.8);
    }
    40% {
      opacity: 1;
      transform: translateY(0) scaleY(1.1);
    }
    60% {
      transform: translateY(5px) scaleY(0.9);
    }
    80% {
      transform: translateY(0) scaleY(1.05);
    }
    100% {
      opacity: 0;
      transform: translateY(15px) scaleY(1);
    }
  }
`;

const Bin = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem 1rem;
  border-radius: 1rem;
  text-align: center;
  color: white;
  font-weight: bold;
  /* Use transient props to avoid passing them to the DOM */
  background-color: ${(props) => props.$bgColor};
  border: 4px solid transparent;
  transition: transform 0.2s ease-in-out, border-color 0.2s ease-in-out,
    box-shadow 0.3s ease, opacity 0.3s ease;
  position: relative;
  opacity: ${(props) => (props.$visible ? 1 : 0)};
  visibility: ${(props) => (props.$visible ? "visible" : "hidden")};

  ${(props) =>
    props.$isActive &&
    css`
      transform: scale(1.02);
      border-color: ${props.$bgColor};
      animation: ${glow(props.$bgColor)} 1.5s ease-in-out infinite;
    `}
`;

const BinContent = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem; /* Consistent spacing */
  h3 {
    margin: 0;
  }
  p {
    font-size: 0.75rem;
    margin: 0;
    font-weight: normal;
  }
`;

const MessageBody = styled.div`
  margin-top: 1rem;
  padding: 0.75rem;
  background-color: rgba(0, 0, 0, 0.25);
  border-radius: 0.5rem;
  width: 95%;
  font-size: 0.8rem;
  font-weight: normal;
  color: #d1d5db;
  border: 1px solid rgba(255, 255, 255, 0.1);
`;

// --- Dashboard Specific Styles ---
const ResetButton = styled.button`
  background-color: #ef4444;
  color: #f9fafb;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 0.75rem;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: background-color 0.2s, transform 0.2s;
  &:hover {
    background-color: #f87171;
    transform: translateY(-2px);
  }
`;

const BottleCard = styled.div`
  background: #111827;
  border-radius: 1.5rem;
  padding: 1rem;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4);
  display: flex;
  flex-direction: row;
  gap: 1.5rem;
  align-items: center;
  width: 90%;
`;

const BottleContainer = styled.div`
  width: 70px;
  height: 170px;
  border: 4px solid #374151;
  border-radius: 35px 35px 15px 15px;
  background-color: #1f2937;
  position: relative;
  overflow: hidden;
  box-shadow: inset 0 4px 10px rgba(0, 0, 0, 0.5);
  flex-shrink: 0;
`;

const BottleFill = styled.div`
  position: absolute;
  bottom: 0;
  width: 100%;
  /* Use transient prop '$level' */
  height: ${(props) => props.$level}%;
  /* Use transient prop '$color' */
  background: linear-gradient(
    180deg,
    ${(props) => props.$color} 0%,
    rgba(0, 0, 0, 0.3) 100%
  );
  border-radius: 35px 35px 0 0;
  transition: height 0.5s ease-in-out;
  display: flex;
  align-items: flex-start;
  justify-content: center;
`;

const FillPercentage = styled.span`
  color: #f9fafb;
  font-weight: bold;
  margin-top: 4px;
  font-size: 0.8rem;
  text-shadow: 0 0 4px rgba(0, 0, 0, 0.7);
`;

const BinDetails = styled.div`
  text-align: left;
  flex-grow: 1;
  h3 {
    font-size: 1.5rem;
    margin: 0 0 0.5rem 0;
  }
`;

const BinFullMessage = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #facc15;
  font-weight: bold;
  margin-top: 0.75rem;
  font-size: 0.875rem;
  animation: ${fadeIn} 0.5s ease-out;
`;

// --- Bin Data ---
const bins = [
  {
    name: "Recycle",
    bgColor: "#0ea5e9",
    desc: "Bottles, cans, paper...",
    icon: <Recycle size={36} strokeWidth={2.5} />,
  },
  {
    name: "Non-Recycle",
    bgColor: "#f97316",
    desc: "Broken toys, dirty items",
    icon: <Trash2 size={36} strokeWidth={2.5} />,
  },
  {
    name: "Organic",
    bgColor: "#84cc16",
    desc: "Food scraps, fruit peels",
    icon: <Leaf size={36} strokeWidth={2.5} />,
  },
];

// --- Main App Component ---
export default function App() {
  const [binLevels, setBinLevels] = useState({
    Recycle: 10,
    "Non-Recycle": 10,
    Organic: 10,
  });

  const videoRef = useRef(null);
  const [activePrediction, setActivePrediction] = useState({
    label: null,
    confidence: null,
  });
  const [webcamStatus, setWebcamStatus] = useState("loading");

  const fetchPredictionFromFrame = async (videoElement) => {
    if (!videoElement || videoElement.readyState < 3) return null; // Check if video has enough data

    const canvas = document.createElement("canvas");
    canvas.width = videoElement.videoWidth;
    canvas.height = videoElement.videoHeight;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);

    return new Promise((resolve) => {
      canvas.toBlob(async (blob) => {
        if (!blob) return resolve(null);

        const formData = new FormData();
        formData.append("file", blob, "frame.jpg");

        try {
          const res = await fetch("http://127.0.0.1:5000/predict", {
            method: "POST",
            body: formData,
          });
          if (!res.ok) return resolve(null);
          const data = await res.json();
          resolve(data);
        } catch (err) {
          console.error("API Error:", err);
          resolve(null);
        }
      }, "image/jpeg");
    });
  };

  const handlePrediction = (binName) => {
    setBinLevels((prev) => {
      const newLevel = Math.min(100, prev[binName] + 10);
      return { ...prev, [binName]: newLevel };
    });
  };

  // FIX: Robust webcam setup and prediction loop
  useEffect(() => {
    let stream = null;
    let intervalId = null;

    const setupWebcam = async () => {
      try {
        const videoElement = videoRef.current;
        if (!videoElement) return;

        stream = await navigator.mediaDevices.getUserMedia({ video: true });
        videoElement.srcObject = stream;

        videoElement.onloadedmetadata = () => {
          videoElement.play().catch((err) => {
            // AbortError is common on fast re-renders, safe to ignore
            if (err.name !== "AbortError") {
              console.error("Webcam play error:", err);
              setWebcamStatus("error");
            }
          });
          setWebcamStatus("active");
        };
      } catch (err) {
        console.error("Error accessing webcam:", err);
        setWebcamStatus("error");
      }
    };

    const runPrediction = async () => {
      const data = await fetchPredictionFromFrame(videoRef.current);
      if (!data || !data.prediction) return;

      const labelMap = {
        Recyclable: "Recycle",
        "Non-Recyclable": "Non-Recycle",
        Organic: "Organic",
      };
      const mappedLabel = labelMap[data.prediction];

      if (mappedLabel && data.confidence > 0.7) {
        handlePrediction(mappedLabel);
        setActivePrediction({
          label: mappedLabel,
          confidence: data.confidence,
        });
        setTimeout(
          () => setActivePrediction({ label: null, confidence: null }),
          2500
        );
      }
    };

    setupWebcam();
    intervalId = setInterval(runPrediction, 3000);

    return () => {
      clearInterval(intervalId);
      if (stream) {
        stream.getTracks().forEach((track) => track.stop());
      }
    };
  }, []); // Empty dependency array ensures this runs only once

  const handleReset = () => {
    setBinLevels({ Recycle: 0, "Non-Recycle": 0, Organic: 0 });
  };

  const getOverlayMessage = () => {
    switch (webcamStatus) {
      case "loading":
        return "Starting camera...";
      case "error":
        return "Camera access denied or unavailable.";
      default:
        return null;
    }
  };

  return (
    <AppWrapper>
      <Header>
        <WelcomeMessage>
          <Logo>
            <img src="/sortyx.png" alt="Sortyx Logo" />
          </Logo>
          <div>
            <h1>Sortyx | Eco-Saver! 🌱</h1>
            <p>Sort it right, keep it bright!</p>
          </div>
        </WelcomeMessage>
        <div style={{ display: "flex", gap: "1rem" }}>
          <ResetButton onClick={handleReset}>
            <RefreshCw size={20} /> Reset Levels
          </ResetButton>
          <NotifyButton>
            <BellRing size={20} /> Notify
          </NotifyButton>
        </div>
      </Header>

      <CombinedBody>
        <SorterColumn>
          <VideoContainer>
            <StyledVideo ref={videoRef} autoPlay playsInline muted />
            {webcamStatus !== "active" && (
              <VideoOverlay>{getOverlayMessage()}</VideoOverlay>
            )}
          </VideoContainer>

          <BinsContainer>
            {bins.map((bin) => {
              const isActive = activePrediction.label === bin.name;
              return (
                <Bin
                  key={bin.name}
                  $bgColor={bin.bgColor}
                  $isActive={isActive}
                  $visible={isActive}
                >
                  <BinContent>
                    {isActive && activePrediction.confidence && (
                      <ConfidenceDisplay $color={bin.bgColor}>
                        {`${Math.round(
                          parseFloat(activePrediction.confidence) * 100
                        )}%`}
                      </ConfidenceDisplay>
                    )}
                    <MessageBody>Item Classified!</MessageBody>
                    {bin.icon}
                    <h3>{bin.name}</h3>
                    <p>{bin.desc}</p>
                  </BinContent>

                  {isActive && (
                    <DroppingArrow $color={bin.bgColor}>
                      <span>⬇</span>
                      <span>⬇</span>
                      <span>⬇</span>
                    </DroppingArrow>
                  )}
                </Bin>
              );
            })}
          </BinsContainer>
        </SorterColumn>

        <DashboardColumn>
          {bins.map((bin) => (
            <BottleCard key={bin.name}>
              <BottleContainer>
                <BottleFill $level={binLevels[bin.name]} $color={bin.bgColor}>
                  {binLevels[bin.name] > 10 && (
                    <FillPercentage>{binLevels[bin.name]}%</FillPercentage>
                  )}
                </BottleFill>
              </BottleContainer>
              <BinDetails>
                <h3>{bin.name}</h3>
                <p>{bin.desc}</p>
                {binLevels[bin.name] >= 100 && (
                  <BinFullMessage>
                    <AlertTriangle size={16} />
                    <span>Bin Full! Please empty.</span>
                  </BinFullMessage>
                )}
              </BinDetails>
            </BottleCard>
          ))}
        </DashboardColumn>
      </CombinedBody>
    </AppWrapper>
  );
}
