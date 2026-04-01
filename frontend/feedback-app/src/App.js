
import React, { useState } from "react";
import { withAuthenticator } from "@aws-amplify/ui-react";
import { get, post } from "aws-amplify/api";
import { fetchAuthSession } from "aws-amplify/auth";
import "./App.css";

function App() {
  const [feedbackText, setFeedbackText] = useState("");
  const [feedbackId, setFeedbackId] = useState("");
  const [responseText, setResponseText] = useState("");
  const [loading, setLoading] = useState(false);

  const API_NAME = "feedbackApi";

  // ✅ POST /feedback
  const sendFeedback = async () => {
    if (!feedbackText.trim()) {
      setResponseText("❌ Please enter feedback text");
      return;
    }

    setLoading(true);
    setResponseText("");

    try {
      const session = await fetchAuthSession();
      const token = session.tokens?.idToken?.toString();

      if (!token) {
        throw new Error("Please log in first");
      }

      const response = await post({
        apiName: API_NAME,
        path: "/feedback",
        options: {
          headers: {
            Authorization: `Bearer ${token}`,
          },
          body: {
            text: feedbackText.trim(),
          },
        },
      }).response;

      console.log('Response status:', response.statusCode);
      console.log('Response body:', response.body);
      let data;
      if (response.body instanceof ReadableStream) {
        const text = await response.body.text();
        console.log('Response text:', text);
        data = JSON.parse(text);
      } else if (typeof response.body === 'string') {
        data = JSON.parse(response.body);
      } else {
        data = response.body;
      }
      console.log('Parsed data:', data);

      if (!data || !data.feedbackId) {
        throw new Error(data?.message || "Backend returned empty feedbackId");
      }

      setFeedbackId(data.feedbackId); // ✅ zapisz ID
      setResponseText(`✅ Feedback submitted!\nFeedback ID: ${data.feedbackId}\n\n⏳ Processing your feedback...`);
    } catch (err) {
      console.error("POST error:", err);
      setResponseText(`❌ Error: ${err.message || "Unknown error"}`);
    } finally {
      setLoading(false);
    }
  };

  // ✅ GET /recommendation
  const getRecommendation = async (retryCount = 0) => {
    if (!feedbackId || feedbackId.trim() === "") {
      setResponseText("❌ Missing feedback ID");
      return;
    }

    setLoading(true);
    setResponseText("");

    try {
      const session = await fetchAuthSession();
      const token = session.tokens?.idToken?.toString();

      if (!token) {
        throw new Error("Please log in first");
      }

      const safeId = encodeURIComponent(feedbackId.trim()); // ✅ zabezpieczenie przed "undefined"

      const response = await get({
        apiName: API_NAME,
        path: `/recommendation?feedbackId=${safeId}`,
        options: {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      }).response;

      let data;
      if (response.body instanceof ReadableStream) {
        const text = await response.body.text();
        data = JSON.parse(text);
      } else if (typeof response.body === 'string') {
        data = JSON.parse(response.body);
      } else {
        data = response.body;
      }

      setResponseText(
        `✅ Recommendation:\n${JSON.stringify(data, null, 2)}`
      );
    } catch (err) {
      console.error("GET error:", err);
      
      // If it's a 404 and we haven't retried too many times, wait and retry
      if (err.message && err.message.includes("Recommendation not found") && retryCount < 5) {
        setResponseText(`⏳ Processing feedback... (attempt ${retryCount + 1}/5)`);
        setLoading(false);
        setTimeout(() => getRecommendation(retryCount + 1), 2000); // Wait 2 seconds before retry
        return;
      }
      
      setResponseText(`❌ Error: ${err.message || "Unknown error"}`);
    } finally {
      if (retryCount >= 5) {
        setLoading(false);
      }
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Feedback App – Lambda Tester</h1>
      </header>

      <main className="App-main">

        {/* POST */}
        <div className="test-section">
          <h2>🧪 Test POST /feedback</h2>
          <textarea
            value={feedbackText || ""}
            onChange={(e) => setFeedbackText(e.target.value)}
            placeholder="Enter your feedback..."
            rows={3}
          />
          <button onClick={sendFeedback} disabled={loading}>
            {loading ? "Submitting..." : "Submit Feedback"}
          </button>
        </div>

        {/* GET */}
        <div className="test-section">
          <h2>🧪 Test GET /recommendation</h2>
          <input
            value={feedbackId || ""}
            onChange={(e) => setFeedbackId(e.target.value)}
            placeholder="Feedback ID"
          />
          <button onClick={getRecommendation} disabled={loading}>
            {loading ? "Loading..." : "Get Recommendation"}
          </button>
        </div>

        {/* RESPONSE */}
        <div className="response-section">
          <h3>📋 Response</h3>
          <pre>{responseText || "Responses will appear here..."}</pre>
        </div>

      </main>
    </div>
  );
}

export default withAuthenticator(App);
