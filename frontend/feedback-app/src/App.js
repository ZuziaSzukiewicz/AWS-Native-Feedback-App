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

  //POST /feedback
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

      setFeedbackId(data.feedbackId);
      setResponseText(`✅ Feedback submitted!\nFeedback ID: ${data.feedbackId}\n\n⏳ Processing your feedback...`);
    } catch (err) {
      console.error("POST error:", err);
      setResponseText(`❌ Error: ${err.message || "Unknown error"}`);
    } finally {
      setLoading(false);
    }
  };

  //GET /recommendation
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

      const safeId = encodeURIComponent(feedbackId.trim());
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
        `✅ Recommendation:\n\n"${data.recommendation}"\n\n📝 Based on your feedback: "${data.sourceText}"\n🆔 Feedback ID: ${data.feedbackId}\n👤 User: ${data.userId}\n📅 Updated: ${new Date(data.updatedAt).toLocaleString()}`
      );
    } catch (err) {
      console.error("GET error:", err);
      
      if (err.message && err.message.includes("Recommendation not found") && retryCount < 5) {
        setResponseText(`⏳ Processing feedback... (attempt ${retryCount + 1}/5)`);
        setLoading(false);
        setTimeout(() => getRecommendation(retryCount + 1), 2000);
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
          <div className="input-group">
            <label htmlFor="feedback-text">Feedback Text:</label>
            <textarea
              id="feedback-text"
              value={feedbackText || ""}
              onChange={(e) => setFeedbackText(e.target.value)}
              placeholder="Enter your feedback..."
              rows={3}
            />
          </div>
          <button onClick={sendFeedback} disabled={loading} className="submit-btn">
            {loading ? "Submitting..." : "Submit Feedback"}
          </button>
        </div>

        {/* GET */}
        <div className="test-section">
          <h2>🧪 Test GET /recommendation</h2>
          <div className="input-group">
            <label htmlFor="feedback-id">Feedback ID:</label>
            <input
              id="feedback-id"
              value={feedbackId || ""}
              onChange={(e) => setFeedbackId(e.target.value)}
              placeholder="Feedback ID"
            />
          </div>
          <button onClick={getRecommendation} disabled={loading} className="get-btn">
            {loading ? "Loading..." : "Get Recommendation"}
          </button>
        </div>

        {/* RESPONSE */}
        <div className="response-section">
          <h3>📋 Response</h3>
          <div className="response-output">{responseText || "Responses will appear here..."}</div>
        </div>

      </main>
    </div>
  );
}

export default withAuthenticator(App);
