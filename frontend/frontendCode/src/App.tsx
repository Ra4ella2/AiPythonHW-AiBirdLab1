import { useState } from 'react'
import './App.css'

function App() {
    const [file, setFile] = useState<File | null>(null)
    const [result, setResult] = useState<any>(null)
    const [history, setHistory] = useState<any[]>([])
    const [search, setSearch] = useState('')
    const [stats, setStats] = useState<any>(null)

    async function analyze() {
        if (!file) {
            alert('Оберіть фото')
            return
        }

        const formData = new FormData()
        formData.append('file', file)

        const response = await fetch('http://127.0.0.1:8000/analyze', {
            method: 'POST',
            body: formData
        })

        const data = await response.json()

        if (!response.ok) {
            alert('Помилка аналізу')
            return
        }

        setResult(data)
        loadHistory()
    }

    async function loadHistory() {
        const response = await fetch('http://127.0.0.1:8000/history')
        const data = await response.json()

        setHistory(data)
    }

    async function searchBird() {
        const response = await fetch(
            `http://127.0.0.1:8000/search?name=${search}`
        )

        const data = await response.json()

        setHistory(data)
    }

    async function deleteBird(id: number) {
        await fetch(
            `http://127.0.0.1:8000/birds/${id}`,
            {
                method: 'DELETE'
            }
        )

        loadHistory()
    }

    async function loadStatistics() {
        const response = await fetch(
            'http://127.0.0.1:8000/statistics'
        )

        const data = await response.json()

        setStats(data)
    }

    async function exportCSV() {
        const response = await fetch(
            'http://127.0.0.1:8000/export',
            {
                method: 'POST'
            }
        )

        const data = await response.json()

        alert(data.message)
    }

    return (
        <div className='main'>

            <h1>AI BIRD LAB</h1>

            <div className='block'>

                <h2>Аналіз фото</h2>

                <input
                    type='file'
                    accept='.jpg,.jpeg,.png'
                    onChange={(e) => {
                        if (e.target.files) {
                            setFile(e.target.files[0])
                        }
                    }}
                />

                <button onClick={analyze}>
                    Проаналізувати
                </button>

            </div>


            {
                result &&

                <div className='block'>

                    <h2>Результат</h2>

                    <p>
                        Вид: {result.best_result.species}
                    </p>

                    <p>
                        Впевненість:
                        {' '}
                        {(result.best_result.confidence * 100).toFixed(2)}%
                    </p>

                    <h3>TOP 3</h3>

                    {
                        result.top_3.map((bird: any, index: number) => (
                            <p key={index}>
                                {index + 1}. {bird.species}
                                {' - '}
                                {(bird.confidence * 100).toFixed(2)}%
                            </p>
                        ))
                    }

                </div>
            }


            <div className='block'>

                <h2>Історія</h2>

                <button onClick={loadHistory}>
                    Показати історію
                </button>

                <div className='search'>

                    <input
                        placeholder='Назва птаха'
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                    />

                    <button onClick={searchBird}>
                        Пошук
                    </button>

                </div>

                {
                    history.map((item) => (
                        <div
                            className='historyItem'
                            key={item.id}
                        >

                            <span>
                                {item.id}. {item.predicted_species}
                            </span>

                            <span>
                                {(item.confidence * 100).toFixed(2)}%
                            </span>

                            <button
                                onClick={() => deleteBird(item.id)}
                            >
                                Видалити
                            </button>

                        </div>
                    ))
                }

            </div>


            <div className='block'>

                <h2>Статистика</h2>

                <button onClick={loadStatistics}>
                    Показати статистику
                </button>

                {
                    stats &&

                    <div className='stats'>

                        <p>
                            Фото: {stats.total_images}
                        </p>

                        {
                            stats.most_common_species &&
                            <p>
                                Найчастіший вид:
                                {' '}
                                {stats.most_common_species.species}
                            </p>
                        }

                        {
                            stats.highest_confidence &&
                            <p>
                                Найвища впевненість:
                                {' '}
                                {(stats.highest_confidence.confidence * 100).toFixed(2)}%
                            </p>
                        }

                        {
                            stats.lowest_confidence &&
                            <p>
                                Найнижча впевненість:
                                {' '}
                                {(stats.lowest_confidence.confidence * 100).toFixed(2)}%
                            </p>
                        }

                    </div>
                }

            </div>


            <div className='block'>

                <h2>CSV</h2>

                <button onClick={exportCSV}>
                    Експорт у CSV
                </button>

            </div>

        </div>
    )
}

export default App