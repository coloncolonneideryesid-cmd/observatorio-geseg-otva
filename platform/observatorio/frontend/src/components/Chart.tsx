import { useEffect, useRef } from 'react'
import * as echarts from 'echarts'

export const PAL = ['#0053BB', '#5B9EF5', '#0D1F3C', '#7a8fb3', '#9db8e8', '#3b6fb8']

/** Gráfica ECharts mínima. `option` se recalcula en cada render; el texto del título es la conclusión. */
export default function Chart({ option, label }: { option: any; label: string }) {
  const el = useRef<HTMLDivElement>(null)
  const inst = useRef<echarts.ECharts | null>(null)
  useEffect(() => {
    if (!el.current) return
    inst.current = echarts.init(el.current)
    const ro = new ResizeObserver(() => inst.current?.resize())
    ro.observe(el.current)
    return () => { ro.disconnect(); inst.current?.dispose() }
  }, [])
  useEffect(() => { inst.current?.setOption({ color: PAL, textStyle: { fontFamily: 'Roboto, Arial' }, ...option }, true) }, [option])
  return <div className="chart" ref={el} role="img" aria-label={label} />
}
