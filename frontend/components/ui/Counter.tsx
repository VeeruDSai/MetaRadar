'use client'

import React, { useEffect } from 'react'
import { motion, useSpring, useTransform, type MotionValue } from 'framer-motion'
import './Counter.css'

interface NumberProps {
  mv: MotionValue<number>
  number: number
  height: number
}

function NumberDigit({ mv, number, height }: NumberProps) {
  const y = useTransform(mv, (latest: number) => {
    const placeValue = latest % 10
    let offset = (10 + number - placeValue) % 10
    let memo = offset * height
    if (offset > 5) {
      memo -= 10 * height
    }
    return memo
  })

  return (
    <motion.span className="counter-number" style={{ y }}>
      {number}
    </motion.span>
  )
}

function normalizeNearInteger(num: number): number {
  const nearest = Math.round(num)
  const tolerance = 1e-9 * Math.max(1, Math.abs(num))
  return Math.abs(num - nearest) < tolerance ? nearest : num
}

function getValueRoundedToPlace(value: number, place: number): number {
  const scaled = value / place
  return Math.floor(normalizeNearInteger(scaled))
}

interface DigitProps {
  place: number | string
  value: number
  height: number
  digitStyle?: React.CSSProperties
}

function Digit({ place, value, height, digitStyle }: DigitProps) {
  const isDecimal = place === '.'
  const valueRoundedToPlace = isDecimal ? 0 : getValueRoundedToPlace(value, Number(place))
  const animatedValue = useSpring(valueRoundedToPlace, {
    stiffness: 120,
    damping: 20,
    mass: 0.8,
  })

  useEffect(() => {
    if (!isDecimal) {
      animatedValue.set(valueRoundedToPlace)
    }
  }, [animatedValue, valueRoundedToPlace, isDecimal])

  if (isDecimal) {
    return (
      <span className="counter-digit" style={{ height, ...digitStyle, width: 'fit-content' }}>
        .
      </span>
    )
  }

  return (
    <span className="counter-digit" style={{ height, ...digitStyle }}>
      {Array.from({ length: 10 }, (_, i) => (
        <NumberDigit key={i} mv={animatedValue} number={i} height={height} />
      ))}
    </span>
  )
}

export interface CounterProps {
  value: number
  fontSize?: number
  padding?: number
  places?: (number | string)[]
  gap?: number
  borderRadius?: number
  horizontalPadding?: number
  textColor?: string
  fontWeight?: React.CSSProperties['fontWeight']
  containerStyle?: React.CSSProperties
  counterStyle?: React.CSSProperties
  digitStyle?: React.CSSProperties
  gradientHeight?: number
  gradientFrom?: string
  gradientTo?: string
  topGradientStyle?: React.CSSProperties
  bottomGradientStyle?: React.CSSProperties
  className?: string
  accessibleLabel?: string
  digitPlaceHolders?: boolean
}

export default function Counter({
  value,
  fontSize = 36,
  padding = 0,
  places,
  gap = 4,
  borderRadius = 4,
  horizontalPadding = 2,
  textColor = 'inherit',
  fontWeight = 'inherit',
  containerStyle,
  counterStyle,
  digitStyle,
  gradientHeight = 12,
  gradientFrom = 'transparent',
  gradientTo = 'transparent',
  topGradientStyle,
  bottomGradientStyle,
  className = '',
  accessibleLabel,
  digitPlaceHolders = false,
}: CounterProps) {
  const numValue = typeof value === 'number' && !isNaN(value) ? Math.max(0, value) : 0
  const height = fontSize + padding

  const computedPlaces = React.useMemo(() => {
    if (places && places.length > 0) return places
    if (digitPlaceHolders) {
      return [100, 10, 1]
    }
    const str = Math.round(numValue).toString()
    return Array.from(str).map((_, i, a) => 10 ** (a.length - i - 1))
  }, [places, numValue, digitPlaceHolders])

  const defaultCounterStyle: React.CSSProperties = {
    fontSize,
    gap,
    borderRadius,
    paddingLeft: horizontalPadding,
    paddingRight: horizontalPadding,
    color: textColor,
    fontWeight,
    direction: 'ltr',
  }

  const defaultTopGradientStyle: React.CSSProperties = {
    height: gradientHeight,
    background: `linear-gradient(to bottom, ${gradientFrom}, ${gradientTo})`,
  }

  const defaultBottomGradientStyle: React.CSSProperties = {
    height: gradientHeight,
    background: `linear-gradient(to top, ${gradientFrom}, ${gradientTo})`,
  }

  return (
    <span className={`counter-container ${className}`} style={containerStyle} aria-hidden="true">
      <span className="counter-counter" style={{ ...defaultCounterStyle, ...counterStyle }}>
        {computedPlaces.map((place, idx) => (
          <Digit
            key={`${place}-${idx}`}
            place={place}
            value={numValue}
            height={height}
            digitStyle={digitStyle}
          />
        ))}
      </span>
      <span className="gradient-container">
        <span className="top-gradient" style={topGradientStyle || defaultTopGradientStyle} />
        <span className="bottom-gradient" style={bottomGradientStyle || defaultBottomGradientStyle} />
      </span>
      {accessibleLabel && <span className="sr-only">{accessibleLabel}</span>}
    </span>
  )
}
