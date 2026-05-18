import { describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { PatientListPager } from './PatientListPager';

describe('PatientListPager', () => {
  it('renders nothing when there is only one page', () => {
    const { container } = render(
      <PatientListPager page={1} pageCount={1} onPageChange={() => {}} />,
    );
    expect(container).toBeEmptyDOMElement();
  });

  it('renders every page number when the count is small', () => {
    render(<PatientListPager page={2} pageCount={4} onPageChange={() => {}} />);
    for (const n of ['1', '2', '3', '4']) {
      expect(screen.getByText(n)).toBeInTheDocument();
    }
    expect(screen.queryByText('More pages')).not.toBeInTheDocument();
  });

  it('collapses long runs with an ellipsis on each side of the window', () => {
    render(<PatientListPager page={10} pageCount={20} onPageChange={() => {}} />);
    // First/last boundary pages plus a one-page window around the current page.
    for (const n of ['1', '9', '10', '11', '20']) {
      expect(screen.getByText(n)).toBeInTheDocument();
    }
    // Pages inside the collapsed runs are not rendered.
    expect(screen.queryByText('5')).not.toBeInTheDocument();
    expect(screen.queryByText('15')).not.toBeInTheDocument();
    expect(screen.getAllByText('More pages')).toHaveLength(2);
  });

  it('marks the current page as active', () => {
    render(<PatientListPager page={3} pageCount={6} onPageChange={() => {}} />);
    expect(screen.getByText('3')).toHaveAttribute('aria-current', 'page');
    expect(screen.getByText('2')).not.toHaveAttribute('aria-current');
  });

  it('invokes onPageChange when a numbered page link is clicked', () => {
    const onPageChange = vi.fn();
    render(
      <PatientListPager page={1} pageCount={3} onPageChange={onPageChange} />,
    );
    fireEvent.click(screen.getByText('3'));
    expect(onPageChange).toHaveBeenCalledWith(3);
  });

  it('invokes onPageChange via the Next control', () => {
    const onPageChange = vi.fn();
    render(
      <PatientListPager page={2} pageCount={5} onPageChange={onPageChange} />,
    );
    fireEvent.click(screen.getByLabelText('Go to next page'));
    expect(onPageChange).toHaveBeenCalledWith(3);
  });

  it('disables Previous on the first page', () => {
    const onPageChange = vi.fn();
    render(
      <PatientListPager page={1} pageCount={5} onPageChange={onPageChange} />,
    );
    const prev = screen.getByLabelText('Go to previous page');
    expect(prev).toHaveAttribute('aria-disabled', 'true');
    expect(screen.getByLabelText('Go to next page')).toHaveAttribute(
      'aria-disabled',
      'false',
    );
    fireEvent.click(prev);
    expect(onPageChange).not.toHaveBeenCalled();
  });

  it('disables Next on the last page', () => {
    const onPageChange = vi.fn();
    render(
      <PatientListPager page={5} pageCount={5} onPageChange={onPageChange} />,
    );
    const next = screen.getByLabelText('Go to next page');
    expect(next).toHaveAttribute('aria-disabled', 'true');
    expect(screen.getByLabelText('Go to previous page')).toHaveAttribute(
      'aria-disabled',
      'false',
    );
    fireEvent.click(next);
    expect(onPageChange).not.toHaveBeenCalled();
  });
});
