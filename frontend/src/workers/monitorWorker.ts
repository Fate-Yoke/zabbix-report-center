// Web Worker 用于后台加载监控数据
// 关键：只在完成后发送一次结果，避免频繁更新阻塞主线程

self.onmessage = async (e) => {
  const { url, token, body } = e.data
  const allData: any[] = []

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {})
      },
      body: JSON.stringify(body)
    })

    if (!response.ok) {
      self.postMessage({ type: 'error', message: `HTTP ${response.status}: ${response.statusText}` })
      return
    }

    const reader = response.body?.getReader()
    if (!reader) {
      self.postMessage({ type: 'error', message: '无法读取响应流' })
      return
    }

    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const event = JSON.parse(line.slice(6))

            if (event.type === 'data') {
              // 只收集数据，不发送进度更新
              allData.push(...event.rows)
            }
            // 忽略其他事件类型，避免频繁通信阻塞主线程
          } catch {
            // 忽略解析错误
          }
        }
      }
    }

    // 所有数据收集完成后，只发送一次结果
    self.postMessage({ type: 'complete', data: allData, count: allData.length })

  } catch (error: any) {
    self.postMessage({ type: 'error', message: error.message })
  }
}
