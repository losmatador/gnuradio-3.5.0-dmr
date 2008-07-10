/* -*- c++ -*- */
/*
 * Copyright 2007 Free Software Foundation, Inc.
 * 
 * This file is part of GNU Radio
 * 
 * GNU Radio is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3, or (at your option)
 * any later version.
 * 
 * GNU Radio is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with GNU Radio; see the file COPYING.  If not, write to
 * the Free Software Foundation, Inc., 51 Franklin Street,
 * Boston, MA 02110-1301, USA.
 */

#ifndef INCLUDED_GR_TOP_BLOCK_IMPL_STS_H
#define INCLUDED_GR_TOP_BLOCK_IMPL_STS_H

#include <gr_top_block_impl.h>
#include <gr_scheduler_thread.h>

/*!
 *\brief Implementation details of gr_top_block
 * \ingroup internal
 *
 * Concrete implementation of gr_top_block using gr_single_threaded_scheduler.
 */
class gr_top_block_impl_sts : public gr_top_block_impl
{
public:
  gr_top_block_impl_sts(gr_top_block *owner);
  ~gr_top_block_impl_sts();

  // Signal scheduler threads to stop
  void stop();

  // Wait for scheduler threads to exit
  void wait();

private:
    
  gr_scheduler_thread_vector_t   d_threads;
  std::vector<gr_basic_block_vector_t> d_graphs;

  void start_threads();
};

#endif /* INCLUDED_GR_TOP_BLOCK_IMPL_STS_H */