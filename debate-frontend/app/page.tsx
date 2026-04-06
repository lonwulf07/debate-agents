"use client";

import { useState } from "react";

interface DebateMessage {
  speaker: string;
  text: string;
}

export default function Home() {
  const [topic, setTopic] = useState("");
  const [messages, setMessages] = useState<DebateMessage[]>([]);
  const [loading, setLoading] = useState(false);

  const startDebate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessages([]);

    try {
      // Removed target_url from the payload
      const response = await fetch("https://lonwulf-debate-agent.hf.space/debate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic }),
      });

      if (!response.body) throw new Error("No response body");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let done = false;

      while (!done) {
        const { value, done: readerDone } = await reader.read();
        done = readerDone;

        if (value) {
          const chunkString = decoder.decode(value, { stream: true });
          const lines = chunkString.split("\n");
          for (const line of lines) {
            if (line.startsWith("data: ")) {
              const jsonString = line.replace("data: ", "");
              try {
                const parsedMessage: DebateMessage = JSON.parse(jsonString);
                setMessages((prev) => [...prev, parsedMessage]);
              } catch (err) {
                console.error("Error parsing JSON chunk:", err);
              }
            }
          }
        }
      }
    } catch (error) {
      console.error("Error starting debate:", error);
      setMessages([
        { speaker: "System", text: "Failed to connect to the backend." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-[100dvh] bg-gray-950 text-gray-100 p-4 sm:p-6 md:p-12 flex flex-col items-center font-sans">
      <div className="w-full max-w-4xl space-y-6 md:space-y-8">
        <h1 className="text-3xl md:text-5xl font-extrabold text-center text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400 pt-4 md:pt-0">
          Autonomous AI Debate Arena
        </h1>

        {/* Simplified Input Form */}
        <form
          onSubmit={startDebate}
          className="flex flex-col space-y-4 bg-gray-900 p-5 md:p-8 rounded-2xl border border-gray-800 shadow-2xl"
        >
          <label
            htmlFor="topic"
            className="text-base md:text-lg font-medium text-gray-300"
          >
            What should the agents research and debate?
          </label>
          <textarea
            id="topic"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="e.g., The viability of using WebAssembly for complex frontend applications."
            className="w-full p-4 rounded-xl bg-gray-950 border border-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 text-white resize-none h-24"
            required
          />
          <button
            type="submit"
            disabled={loading}
            className="w-full py-4 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-xl transition-all disabled:opacity-50"
          >
            {loading
              ? "Agents are Googling and synthesizing..."
              : "Initiate Autonomous Debate"}
          </button>
        </form>

        {/* The Debate Chat Arena */}
        {(messages.length > 0 || loading) && (
          <div className="bg-gray-900 p-5 md:p-8 rounded-2xl border border-gray-800 shadow-xl space-y-6">
            {messages.map((msg, index) => {
              // Determine styling based on speaker identity
              const isOptimist = msg.speaker.includes("Optimist");
              const isSkeptic = msg.speaker.includes("Skeptic");
              const isJudge = msg.speaker.includes("Judge");

              // Dynamic CSS classes for alignment and colors
              let containerAlignment = "items-start";
              let bubbleStyle = "bg-gray-800 border-gray-700 text-gray-200"; // Fallback

              if (isOptimist) {
                containerAlignment = "items-start";
                bubbleStyle =
                  "bg-blue-900/50 border border-blue-700/50 rounded-tr-2xl rounded-br-2xl rounded-bl-2xl text-blue-50";
              } else if (isSkeptic) {
                containerAlignment = "items-end";
                bubbleStyle =
                  "bg-emerald-900/50 border border-emerald-700/50 rounded-tl-2xl rounded-bl-2xl rounded-br-2xl text-emerald-50";
              } else if (isJudge) {
                // Judge gets centered, full-width treatment with a purple/gold hue
                containerAlignment = "items-center w-full";
                bubbleStyle =
                  "bg-indigo-900/40 border-2 border-indigo-500/50 rounded-2xl text-indigo-50 shadow-[0_0_15px_rgba(99,102,241,0.2)] w-full";
              }

              return (
                <div
                  key={index}
                  className={`flex flex-col w-full ${containerAlignment} animate-fade-in-up mt-8`}
                >
                  <span className="text-xs font-bold tracking-wider uppercase text-gray-400 mb-2 px-2">
                    {msg.speaker}
                  </span>
                  <div
                    className={`max-w-[90%] md:max-w-[85%] p-5 md:p-6 ${bubbleStyle}`}
                  >
                    <div className="prose prose-invert prose-sm md:prose-base max-w-none">
                      {msg.text.split("\n").map((paragraph, i) => (
                        <p key={i} className="mb-3 last:mb-0 leading-relaxed">
                          {paragraph}
                        </p>
                      ))}
                    </div>
                  </div>
                </div>
              );
            })}

            {loading && (
              <div className="flex justify-center py-6">
                <span className="flex items-center gap-3 text-gray-400 font-medium animate-pulse">
                  <svg
                    className="animate-spin h-5 w-5 text-blue-500"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    ></circle>
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    ></path>
                  </svg>
                  Agents are actively researching and evaluating...
                </span>
              </div>
            )}
          </div>
        )}
      </div>
    </main>
  );
}
