import React from 'react';
import { render, screen } from '@testing-library/react';
import { Button } from '@/shared/ui';

describe('Button', () => {
  it('renders button children', () => {
    render(<Button>Click me</Button>);

    expect(screen.getByRole('button', { name: 'Click me' })).toBeInTheDocument();
  });
});
