import { useState } from 'react'
import ChatInterface from './components/ChatInterface'
import DataPreview from './components/DataPreview'
import './App.css'

function App() {
  return (
    <div className="app">
      <header className="app-header">
        <h1>NYC Uber/Lyft Data Chatbot</h1>
      </header>
      <main className="app-main">
        <DataPreview />
        <ChatInterface />
      </main>
    </div>
  )
}

export default App

