import streamlit as st
import os
import yfinance as yf
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import Tool
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from technical_tools import get_technical_analysis
from news_tools import get_news_sentiment

# --- SETUP & STATE MANAGEMENT ---
api_key = os.environ.get('GOOGLE_API_KEY')
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2, max_output_tokens=2048, google_api_key=api_key)

if "latest_report" not in st.session_state:
    st.session_state.latest_report = ""
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

# --- TOOLS & AGENT ---
tools = [
    Tool(name="Technical_Analyst", func=get_technical_analysis, description="Use to get price, RSI, and trend of a stock."),
    Tool(name="News_Sentiment_Analyst", func=get_news_sentiment, description="Use to get recent news headlines and sentiment.")
]

system_message = """You are a Senior Market Analyst named 'Scout'.
You MUST use the tools to fetch data.
After using the tools, you write a COMPLETE, multi-paragraph recommendation report.
Structure your final answer clearly with bullet points and a concluding sentence."""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_message),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)

# --- CACHING THE AI ENGINE ---
# This saves the API response for 1 hour (3600 seconds) so you don't burn your free limits!
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_scout_report(ticker_symbol):
    return agent_executor.invoke({"input": f"Analyze {ticker_symbol} and give me a recommendation."})

# --- UI DESIGN ---
st.set_page_config(page_title="Market Scout AI Terminal", layout="wide", page_icon="📈")
st.title("🦅 Market Scout AI Terminal")

ticker = st.text_input("Enter Ticker (e.g., TSLA, NVDA):").upper()

tab1, tab2, tab3 = st.tabs(["📊 Market Report", "🤖 Chat with Scout", "⚡ Trade Desk"])

# --- TAB 1: THE DASHBOARD ---
with tab1:
    if st.button("Scout Market") and ticker:
        with st.spinner(f"Scouting {ticker}... Analyzing charts and reading news..."):
            try:
                # WE CALL THE CACHED FUNCTION HERE INSTEAD OF THE AGENT DIRECTLY
                response = fetch_scout_report(ticker)
                
                # Visual Metrics
                hist = yf.Ticker(ticker).history(period="1mo")
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                    prev_price = hist['Close'].iloc[-2]
                    price_change = current_price - prev_price
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Current Price", f"${current_price:.2f}", f"{price_change:.2f}")
                    col2.metric("Trading Volume", f"{int(hist['Volume'].iloc[-1]):,}")
                    col3.metric("Data Period", "1 Month")
                    st.line_chart(hist['Close'])
                
                st.divider()

                # Clean Output Parsing
                final_answer = response.get("output", "")
                display_text = ""
                if isinstance(final_answer, list):
                    for item in final_answer:
                        if isinstance(item, dict) and "text" in item:
                            display_text += item["text"]
                        elif isinstance(item, str):
                            display_text += item
                else:
                    display_text = str(final_answer)

                if display_text.strip():
                    clean_text = display_text.replace("$", "\\$")
                    st.markdown(f"### 🤖 Scout's Final Recommendation\n{clean_text}")
                    
                    # Save to memory for the Chatbot
                    st.session_state.latest_report = clean_text
                    st.session_state.chat_messages = [{"role": "assistant", "content": f"I just generated a report on {ticker}. What questions do you have?"}]
                else:
                    st.warning("The AI returned an empty response.")
                    
                with st.expander("View Raw API Response"):
                    st.write(response)

            except Exception as e:
                st.error(f"An error occurred: {e}")

# --- TAB 2: EDUCATIONAL CHATBOT ---
with tab2:
    st.markdown("### 🎓 Ask Scout Questions")
    if not st.session_state.latest_report:
        st.info("Generate a market report first so I have context to chat with you about!")
    else:
        for msg in st.session_state.chat_messages:
            st.chat_message(msg["role"]).write(msg["content"])
            
        if user_query := st.chat_input("Ask a question about the report or trading terms..."):
            st.session_state.chat_messages.append({"role": "user", "content": user_query})
            st.chat_message("user").write(user_query)
            
            chat_context = f"You are Scout, an educational trading AI. Based on this recent report you wrote:\n\n{st.session_state.latest_report}\n\nAnswer the user's question simply and educationally: {user_query}"
            
            with st.spinner("Thinking..."):
                chat_response = llm.invoke(chat_context)
                bot_reply = chat_response.content.replace("$", "\\$")
                
                st.session_state.chat_messages.append({"role": "assistant", "content": bot_reply})
                st.chat_message("assistant").write(bot_reply)

# --- TAB 3: TRADE EXECUTION ---
with tab3:
    st.markdown("### ⚡ Paper Trading Simulator")
    if not st.session_state.latest_report:
        st.info("Run a scan on a ticker in the Dashboard first to unlock trading options.")
    else:
        st.write("Based on Scout's analysis, would you like to execute a simulated trade?")
        
        trade_action = st.radio("Select Action:", ["Buy", "Sell", "Hold"])
        shares = st.number_input("Number of Shares:", min_value=1, value=10)
        
        if st.button("Execute Simulated Trade"):
            st.success(f"✅ Simulated Order Placed: {trade_action} {shares} shares of {ticker}.")
            st.info("Note: To trade real capital, you would connect a brokerage API here to replace this simulation logic.")
