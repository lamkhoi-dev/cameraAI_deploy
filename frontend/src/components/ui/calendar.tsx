import * as React from "react"
import { DayPicker } from "react-day-picker"
import { cn } from "@/lib/utils"
import "react-day-picker/style.css"

export type CalendarProps = React.ComponentProps<typeof DayPicker>

function Calendar({ className, ...props }: CalendarProps) {
  return (
    <div className={cn("[&_.rdp-root]:text-zinc-200 [&_.rdp-day_button]:text-zinc-300 [&_.rdp-day_button:hover]:bg-zinc-800 [&_.rdp-selected_.rdp-day_button]:bg-blue-600 [&_.rdp-selected_.rdp-day_button]:text-white [&_.rdp-today_.rdp-day_button]:bg-zinc-800 [&_.rdp-outside_.rdp-day_button]:text-zinc-600 [&_.rdp-chevron]:fill-zinc-400 [&_.rdp-month_caption]:text-zinc-200 [&_.rdp-weekday]:text-zinc-500 [&_.rdp-range_middle_.rdp-day_button]:bg-zinc-800", className)}>
      <DayPicker {...props} />
    </div>
  )
}
Calendar.displayName = "Calendar"

export { Calendar }
